import asyncio
import platform
import queue
import threading
import time
from asyncio.subprocess import Process
from collections import deque
from typing import Dict, List, Tuple, Callable

import networkx as nx
import os
import subprocess
from src.graph_types import GraphType
from src.paths import PROJECT_ROOT


def g6(graph: nx.Graph, subgraph_nodes: list) -> bytes:
    """
    Convert a subgraph into graph6 format without using intermediary strings and adjacency matrix.
    """
    # Step 1: Compute N(n), the graph size character
    n = len(subgraph_nodes)

    current_group = bit_count = 0
    bit_vector = bytearray()
    N = n + 63  # add 63 to the number of nodes
    bit_vector.append(N)

    # Step 2: Compute R(x).
    # For undirected: read upper triangle of the matrix, column by column
    for c in range(n):
        for r in range(c):
            if graph.has_edge(subgraph_nodes[r], subgraph_nodes[c]):
                current_group = (current_group << 1) | 1
            else:
                current_group = current_group << 1

            bit_count += 1

            if bit_count == 6:
                bit_vector.append(current_group + 63)
                current_group = 0
                bit_count = 0

    # Step 3: Pad bit vector with zeros to make its length a multiple of 6
    if bit_count > 0:
        current_group = current_group << (6 - bit_count)
        bit_vector.append(current_group + 63)

    # Step 4: Convert each group of 6 bits into an ASCII character laser
    return bytes(bit_vector)


def d6(graph: nx.Graph, subgraph_nodes: list) -> bytes:
    """Convert a directed subgraph into digraph6 format."""
    # Step 1: Compute N(n), the graph size character
    n = len(subgraph_nodes)

    current_group = bit_count = 0
    bit_vector = bytearray()
    N = n + 63  # add 63 to the number of nodes
    bit_vector.append(38)  # & character for directed graphs
    bit_vector.append(N)

    # Step 2: Compute R(x).
    # For directed: read the matrix row by row
    for r in range(n):
        for c in range(n):
            if graph.has_edge(subgraph_nodes[r], subgraph_nodes[c]):
                current_group = (current_group << 1) | 1
            else:
                current_group = current_group << 1

            bit_count += 1

            if bit_count == 6:
                bit_vector.append(current_group + 63)
                current_group = 0
                bit_count = 0

    # Step 3: Pad bit vector with zeros to make its length a multiple of 6
    if bit_count > 0:
        current_group = current_group << (6 - bit_count)
        bit_vector.append(current_group + 63)

    # Step 4: Convert each group of 6 bits into an ASCII character later
    return bytes(bit_vector)


def basic_graph_label(nx_graph: nx.Graph, subgraph_nodes: list, graph_type: GraphType) -> bytes:
    """
    Label a graph in either graph6 (undirected) or digraph6 (directed) format.
    """
    if graph_type == GraphType.UNDIRECTED:
        return g6(nx_graph, subgraph_nodes)
    return d6(nx_graph, subgraph_nodes)


def _get_labelg_path() -> str:
    """
    Resolves the path to the labelg executable based on the current OS and architecture,
    so both linux and macOS binaries are supported.
    Expected folder structure: NetMotif/bin/{os}/{arch}/labelg
    Assumes this file is in src/label.py

    For example:
    - Linux binaries will go to:
      NetMotif/bin/linux/amd64/labelg
    - macOS binaries will go to:
      NetMotif/bin/darwin/arm64/labelg
    """
    system = platform.system().lower()
    arch = platform.machine().lower()

    if arch == "x86_64" or arch == "amd64":
        arch = "amd64"
    elif arch == "aarch64":
        arch = "arm64"

    labelg = "labelg.exe" if system == "windows" else "labelg"

    return os.path.join(PROJECT_ROOT, "bin", system, arch, labelg)


class AsyncLabelg[Info]:
    def __init__(self, callback: Callable[[str, Info], None]):
        """
        Allows asynchronously labeling subgraphs using labelg.
        Pass non-canonical labels and extra data (e.g., subgraph nodes) to the label function.
        Then, when ready, the callback will be called with the canonical label and extra data that
        was previously provided.

        Note:
          * The finish function must be called, or else some labels will be skipped.
          * The label function may block if too many labels are being processed at once.

        :param callback: the function to call when a label is ready.
        """

        # How many labels to send to labelg at once.
        self._batch_size = 1000
        # How many batches can be processing before pausing.
        self._max_batches = 10
        # This is an arbitrary time to wait for processing before
        # throwing an error.
        # Its sole purpose is to prevent memory leaks.
        self._waiting_time = 60

        self._callback = callback

        # Non-canonical label -> canonical label
        self._canonical_map: Dict[bytes, str] = {}
        # Non-canonical label -> extra data
        self._info_map: Dict[bytes, List[Info]] = {}

        # The batch currently being built by the label function.
        self._cur_in_batch: List[bytes] = []

        # Batched labels that should be canonicalized.
        self._batch_input: asyncio.Queue[List[bytes] | None] = asyncio.Queue()
        # Batched maps of uncanonical labels to canonical labels.
        # This is a list and not a dict because it makes it easier to uphold
        # _outstanding_batches' same number of batches contract.
        self._batch_output: queue.Queue[List[Tuple[bytes, str]]] = queue.Queue()

        # This counter approach is safe as long as batches are always _batch_size in size,
        # except for the last batch, and the same number of batches send to _batch_input are
        # received from _batch_output.
        self._outstanding_batches: int = 0

        # These are owned by the worker thread, and must be accessed only from there.
        # The worker thread also shouldn't access anything that it doesn't own and which
        # isn't thread-safe (the queues are thread-safe).

        # The labelg process.
        self._w_process: Process | None = None
        # The labels that are currently being processed, in the order they were
        # submitted to labelg.
        self._w_labels_processing: deque[bytes] = deque()
        # Whether the worker thread is done receiving labels from the main thread,
        # and should exit soon.
        self._w_worker_done = False
        # Any error that occurred in the worker thread.
        self._w_worker_error: Exception | None = None

        # Start the process and worker thread.
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._thread_main, daemon=True)

        self._thread.start()

    def label(self, label: bytes, info: Info):
        """
        Sends a label to labelg for processing.
        This may block if there isn't space left, and will also run the callback if
        any canonical labels are available.

        :param label: the label to canonicalize.
        :param info: info associated with the label, which should be passed to the callback.
        """

        if label in self._canonical_map:
            self._callback(self._canonical_map[label], info)
            return

        self._cur_in_batch.append(label)
        self._info_map.setdefault(label, []).append(info)

        if len(self._cur_in_batch) >= self._batch_size:
            # Prevent endlessly building up data.
            # Each call to _handle_output will decrement _outstanding_batches,
            # and will pause the thread until a piece of output is available.
            while self._outstanding_batches >= self._max_batches:
                # If the queue shuts down while we're blocking, then
                # try to print the error that caused the shutdown, if any.
                # This makes debugging slightly nicer.
                try:
                    output_batch = self._batch_output.get(timeout=self._waiting_time)
                except queue.ShutDown:
                    if self._w_worker_error is not None:
                        raise self._w_worker_error
                    raise queue.ShutDown

                self._handle_output(output_batch)

            self._loop.call_soon_threadsafe(self._batch_input.put_nowait, self._cur_in_batch)
            self._cur_in_batch = []
            self._outstanding_batches += 1

        # If there's data available, this is a good place to process it.
        while not self._batch_output.empty():
            self._handle_output(self._batch_output.get_nowait())

    def finish(self):
        """
        Marks the labeling as done and waits for all outstanding labels to be processed.
        """

        # We need to handle the last (partial) batch of labels.
        if self._cur_in_batch:
            self._loop.call_soon_threadsafe(self._batch_input.put_nowait, self._cur_in_batch)
            self._cur_in_batch = []
            self._outstanding_batches += 1

        # Tell the thread to stop processing labels.
        self._loop.call_soon_threadsafe(self._batch_input.put_nowait, None)

        # Clean up everything.
        # We should kill the process after the worker
        # is closed to avoid race conditions.
        self._thread.join(timeout=self._waiting_time)
        self._loop.close()
        try:
            self._w_process.kill()
        except ProcessLookupError:
            # The process already exited.
            pass

        # If an error occurred, throw it so we can debug it.
        if self._w_worker_error is not None:
            raise self._w_worker_error

        # Otherwise, handle the remaining data sent from
        # the worker.
        while self._outstanding_batches > 0:
            # No blocking here, since the worker thread is dead.
            # If an item is missing, it's always an error.
            self._handle_output(self._batch_output.get(block=False))

    def _handle_output(self, output: List[Tuple[bytes, str]]):
        """
        Handles a single output batch from the worker thread, running
        the callback for each label.

        :param output: the output batch from the worker thread / labelg.
        """

        for label, canon_label in output:
            self._canonical_map[label] = canon_label

            # There might be duplicate labels in the output, so
            # we might have already processed this label.
            if label in self._info_map:
                for info in self._info_map[label]:
                    self._callback(canon_label, info)
                del self._info_map[label]

        self._outstanding_batches -= 1

    def _thread_main(self):
        """
        The main function for the worker thread.
        Runs _w_run_thread and stores any errors in _w_worker_error.
        When this ends, the event loop will be stopped.
        """

        try:
            self._loop.run_until_complete(self._w_run_thread())
        except Exception as e:
            self._w_worker_error = e

    async def _w_run_thread(self):
        """
        Starts the processing tasks in the worker thread.
        Should be run on the event loop and in the worker thread.
        """

        await self._w_start_labelg()
        await asyncio.gather(self._w_handle_read(), self._w_handle_write())

    async def _w_handle_read(self):
        """
        Reads canonical labels from labelg and sends them to the output queue in batches.
        """

        cur_batch: List[Tuple[bytes, str]] = []

        async for canon_label in self._w_process.stdout:
            original_label = self._w_labels_processing.popleft()
            cur_batch.append((original_label, canon_label.decode("ascii").strip()))

            if len(cur_batch) >= self._batch_size:
                self._batch_output.put(cur_batch)
                cur_batch = []

            # If we're done writing labels, then we can stop reading only
            # after all outstanding labels have been processed.
            if self._w_worker_done and len(self._w_labels_processing) == 0:
                break

        # There will be some labels remaining that didn't make a full batch.
        if cur_batch:
            self._batch_output.put(cur_batch)

        # No more output.
        # If something tries to "get" from the queue, this makes it
        # throw an error instead of blocking forever.
        self._batch_output.shutdown()

        # If we stopped unexpectedly, we should throw an error for debugging
        # and to avoid being stuck endlessly.
        if self._w_process.returncode is not None and self._w_process.returncode != 0:
            raise RuntimeError(f"labelg exited with code {self._w_process.returncode}")

    async def _w_handle_write(self):
        """
        Processes _batch_input and passes non-canonical labels to labelg.
        """

        while True:
            batch = await self._batch_input.get()
            if batch is None:
                # We're done processing labels.
                # I'm not sure if this is necessary, but
                # it will signal to labelg that it's done processing.
                self._w_process.stdin.close()

                # The reader needs to be informed so that it can stop itself.
                self._w_worker_done = True
                self._batch_input.shutdown()
                break

            if batch:
                self._w_labels_processing.extend(batch)
                self._w_process.stdin.write(b"\n".join(batch) + b"\n")
                await self._w_process.stdin.drain()

    async def _w_start_labelg(self):
        """
        Starts the labelg process.
        """

        label_g = _get_labelg_path()
        if os.path.isfile(label_g):
            os.chmod(label_g, 0o755)
        else:
            raise RuntimeError("labelg executable not found")

        self._w_process = await asyncio.create_subprocess_exec(
            label_g,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            # Useful to remove this line for debugging.
            stderr=asyncio.subprocess.DEVNULL,
        )
