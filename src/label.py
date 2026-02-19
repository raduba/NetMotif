import time
import networkx as nx
import os
import subprocess
import streamlit as st
from src.graph_types import GraphType
from pyinstrument import Profiler
import atexit

def graph6(graph: nx.Graph) -> str:
    """
    Convert a subgraph into graph6 format.

    Parameters:
        graph (nx.Graph): A NetworkX graph.

    Returns:
        str: The graph6 encoded string.
    """
    # Step 1: Compute N(n), the graph size character
    graph_size = graph.order()  # number of nodes in the graph
    vertices = list(graph.nodes())
    n = len(vertices)

    if graph_size == 0:
        return ""  # empty graph
    elif graph_size == 1:
        return ""  # single-node graph

    N = chr(graph_size + 63)  # add 63 to graph_size

    # Step 2: Compute R(x). Create bit vector from the upper triangle of the
    # adjacency matrix
    # For undirected: read upper triangle of the matrix, column by column
    bit_vector = []
    adj_matrix = [[0 for _ in range(n)] for _ in range(n)]
    for r in range(len(adj_matrix)):
        for c in range(len(adj_matrix[r])):
            if graph.has_edge(vertices[r], vertices[c]):
                adj_matrix[r][c] = 1
    for col in range(len(adj_matrix[0])):
        for row in range(col):
            bit_vector.append(adj_matrix[row][col])

    # Step 3: Pad bit vector with zeros to make its length a multiple of 6
    while len(bit_vector) % 6 != 0:
        bit_vector.append(0)

    # Step 4: Convert each group of 6 bits into an ASCII character for encoding
    R = ""
    for i in range(0, len(bit_vector), 6):
        group = bit_vector[i : i + 6]
        group_value = sum((bit << (5 - idx)) for idx, bit in enumerate(group))
        R += chr(group_value + 63)
    return N + R


def g6(graph: nx.Graph) -> str:
    """
    Convert a subgraph into graph6 format without using intermediary strings and adjacency matrix.

    Parameters:
        graph (nx.Graph): A NetworkX graph.

    Returns:
        str: The graph6 encoded string.
    """
    # Step 1: Compute N(n), the graph size character
    vertices = list(graph.nodes())
    n = len(vertices)

    current_group = bit_count = 0
    bit_vector = bytearray()
    N = n + 63  # add 63 to the number of nodes
    bit_vector.append(N)

    # Step 2: Compute R(x). Create bit vector from the upper triangle of the
    # adjacency matrix
    # For undirected: read upper triangle of the matrix, column by column
    for c in range(n):
        for r in range(c):
            if graph.has_edge(vertices[r], vertices[c]):
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

    # Step 4: Convert each group of 6 bits into an ASCII character for encoding
    return bit_vector.decode("ascii")


def digraph6(graph: nx.DiGraph) -> str:
    """
    Convert a directed subgraph into digraph6 format.

    Parameters:
        graph (nx.Graph): A NetworkX graph.

    Returns:
        str: The digraph6 encoded string.
    """
    # Step 1: Compute N(n), the graph size character
    graph_size = graph.order()
    vertices = list(graph.nodes)

    if graph_size == 0:
        return ""  # empty graph
    elif graph_size == 1:
        return ""  # single-node graph

    N = chr(graph_size + 63)

    # Step 2: Compute R(x). Create bit vector from the upper triangle of the
    # adjacency matrix
    # For directed: read the matrix row by row
    bit_vector = []
    for r in vertices:
        for c in vertices:
            if graph.has_edge(r, c):
                bit_vector.append(1)
            else:
                bit_vector.append(0)

    # Step 3: Pad bit vector with zeros to make its length a multiple of 6
    while len(bit_vector) % 6 != 0:
        bit_vector.append(0)

    # Step 4: Convert each group of 6 bits to an ASCII character for encoding
    R = ""
    for i in range(0, len(bit_vector), 6):
        group = bit_vector[i : i + 6]
        group_value = sum((bit << (5 - idx)) for idx, bit in enumerate(group))
        R += chr(group_value + 63)

    return chr(38) + N + R


def toLabelg(label: str):
    label_g = "labelg"  # Name of the executable

    try:
        result = subprocess.run(
            [label_g],
            input=label + "\n",
            text=True,
            capture_output=True,
            check=True,
        )

        # if subprocess runs correctly
        if result.returncode == 0:
            labelg_output = result.stdout.rstrip()
        else:
            st.write(
                "Subprocess failed with return code:",
                result.returncode,
            )
            st.error(result.stderr)

    except subprocess.CalledProcessError as e:
        st.write("error running labelg:")
        st.write(e.stderr)

    return labelg_output


def collect_labelg(labels: list[str]) -> list[str]:
    """
    Collect the canonical label for all the labels using only one labelg process, instead of
    spawning a process for each label.
    Expect the labelg executable to exists in the root directory.
    Pass the labels list with each label on its own line, labelg will maintain the order in the
    output results.
    """
    start_time = time.perf_counter()
    label_g = "labelg"

    unique_labels = list(set(labels))
    labelg_input = "\n".join(unique_labels)
    result = subprocess.run(
        [label_g],
        input=labelg_input,
        text=True,
        capture_output=True,
        check=True,
    )

    # if subprocess runs correctly, return the output lines
    if result.returncode != 0:
        raise RuntimeError(f"labelg subprocess failed with return code: {result.returncode}")

    result_labels = result.stdout.rstrip().split("\n")
    canonical_labels = dict(zip(unique_labels, result_labels))
    print(f"Time to label {len(labels)} labels: {(time.perf_counter() - start_time):.6f} s")
    return [canonical_labels[label] for label in labels]


def get_basic_graph_label(nx_graph: nx.Graph, graph_type: GraphType) -> str:
    """
    Label a graph in either graph6 (undirected) or digraph6 (directed) format.
    """
    if graph_type == GraphType.UNDIRECTED:
        return g6(nx_graph)
    if graph_type == GraphType.DIRECTED:
        return digraph6(nx_graph)


def get_graph_label(nx_graph: nx.Graph, graph_type: GraphType) -> str:
    """
    Label a graph in labelg format.
    """
    # for linux
    return toLabelg(get_basic_graph_label(nx_graph, graph_type))

# Records a flamegraph for the worker process' entire execution.
# Pass to the pool as initializer=_init_worker.
# The pool must be closed manually, like this:
#     pool.close()
#     pool.join()
# Otherwise, it won't be shutdown gracefully and the atexit
# handler won't run.
def _init_worker():
    profiler = Profiler()
    profiler.start()

    def on_exit():
        profiler.stop()
        profiler.open_in_browser()
    atexit.register(on_exit)
