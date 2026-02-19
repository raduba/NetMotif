import time
import networkx as nx
import os
import subprocess
import streamlit as st
from collections import defaultdict
import atexit
from pyinstrument import Profiler
import multiprocessing
from multiprocessing import Pool
from src.graph_types import GraphType


def print_labelg(graph_type, subgraph_list: list[nx.Graph]):
    """
    Takes in esu subgraph list and outputs labels into a .txt file.
    """
    output_dir = "out"
    labels_file_output = os.path.join(output_dir, "labels.txt")

    # Ensure output folder exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    label_counter = defaultdict(int)

    # Convert to graph6 type
    with open(labels_file_output, "w") as file:
        for subgraph in subgraph_list:
            label = get_basic_graph_label(subgraph, graph_type)
            label_counter[label] += 1
            label = label + "\n"
            file.writelines(label)

    # Convert to labelg
    label_g = "labelg"  # Name of the executable

    labelg_output_file = os.path.join(output_dir, "labelg_output.txt")
    try:
        subprocess.run(
            [label_g, labels_file_output, labelg_output_file],
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        st.write("error running labelg:")
        st.write(e.stderr)

    return labelg_output_file


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
        return graph6(nx_graph)
    if graph_type == GraphType.DIRECTED:
        return digraph6(nx_graph)


def get_graph_label(nx_graph: nx.Graph, graph_type: GraphType) -> str:
    """
    Label a graph in labelg format.
    """
    # for linux
    return toLabelg(get_basic_graph_label(nx_graph, graph_type))


def _apply_basic_label_worker(args):
    """
    Worker arguments of type (nx.Graph | nx.DiGraph, GraphType) so we can compute the subgraph
    labels in parallel
    """
    g, graph_type = args
    return get_basic_graph_label(g, graph_type)

# Records a flamegraph for the worker process' entire execution.
# The process name check is a bit dubious, but works for debugging.
def _init_worker():
    return

    profiler = Profiler()
    profiler.start()

    def on_exit():
        profiler.stop()
        profiler.open_in_browser()
    atexit.register(on_exit)


def calculate_basic_labels(subgraphs):
    pool = Pool(processes=8, initializer=_init_worker)
    result = pool.map(_apply_basic_label_worker, subgraphs)
    # Must be done manually, otherwise the process doesn't
    # end gracefully and atexit doesn't run.
    pool.close()
    pool.join()
    return result
