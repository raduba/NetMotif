import time
import networkx as nx
import subprocess
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

g6_cache = dict()

def g6(graph: nx.Graph, sg_nodes: list[int]) -> str:
    """
    Convert a subgraph into graph6 format without using intermediary strings and adjacency matrix.

    Parameters:
        graph (nx.Graph): The parent graph.
        sg_nodes (list[int]): A list of nodes in the parent which form a subgraph.

    Returns:
        str: The graph6 encoded string.
    """
    # Step 1: Compute N(n), the graph size character
    n = len(sg_nodes)

    bit_count = 0
    # This has two imaginary leading zeros.
    bits = n + 63 # add 63 to the number of nodes
    num_bytes = 1

    # Step 2: Compute R(x). Create bit vector from the upper triangle of the
    # adjacency matrix
    # For undirected: read upper triangle of the matrix, column by column
    for c in range(n):
        for r in range(c):
            if bit_count == 0:
                # This section needs two leading zeros.
                bits <<= 2

            if sg_nodes[c] in graph._adj[sg_nodes[r]]:
                bits = (bits << 1) | 1
            else:
                bits = bits << 1

            bit_count += 1

            if bit_count == 6:
                bits += 63
                num_bytes += 1
                bit_count = 0

    # Step 3: Pad bit vector with zeros to make its length a multiple of 6
    if bit_count > 0:
        bits = bits << (6 - bit_count)
        bits += 63
        num_bytes += 1

    if bits not in g6_cache:
        # Step 4: Convert each group of 6 bits into an ASCII character for encoding
        g6_cache[bits] = bits.to_bytes(num_bytes, "big").decode("ascii")

    return g6_cache[bits]

d6_cache = dict()

def digraph6(graph: nx.DiGraph, sg_nodes: list[int]) -> str:
    """
    Convert a directed subgraph into digraph6 format.

    Parameters:
        graph (nx.Graph): The parent graph.
        sg_nodes (list[int]): A list of nodes in the parent which form a subgraph.

    Returns:
        str: The digraph6 encoded string.
    """
    # Step 1: Compute N(n), the graph size character
    graph_size = len(sg_nodes)

    if graph_size == 0:
        return ""  # empty graph
    elif graph_size == 1:
        return ""  # single-node graph

    bit_count = 0
    # This has two imaginary leading zeros.
    bits = graph_size + 63
    num_bytes = 1

    # Step 2: Compute R(x). Create bit vector from the full adjacency matrix
    # For directed: read the matrix row by row
    for r in sg_nodes:
        for c in sg_nodes:
            if bit_count == 0:
                # This section needs two leading zeros.
                bits <<= 2

            if graph.has_edge(r, c):
                bits = (bits << 1) | 1
            else:
                bits = bits << 1

            bit_count += 1

            if bit_count == 6:
                bits += 63
                num_bytes += 1
                bit_count = 0

    # Step 3: Pad bit vector with zeros to make its length a multiple of 6
    if bit_count > 0:
        bits = bits << (6 - bit_count)
        bits += 63
        num_bytes += 1

    if bits not in d6_cache:
        # Step 4: Convert each group of 6 bits into an ASCII character for encoding
        d6_cache[bits] = "&" + bits.to_bytes(num_bytes, "big").decode("ascii")

    return d6_cache[bits]

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


def get_basic_graph_label(nx_graph: nx.Graph, sg_nodes: list[int], graph_type: GraphType) -> str:
    """
    Label a graph in either graph6 (undirected) or digraph6 (directed) format.
    """
    if graph_type == GraphType.UNDIRECTED:
        return g6(nx_graph, sg_nodes)
    if graph_type == GraphType.DIRECTED:
        return digraph6(nx_graph, sg_nodes)


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
