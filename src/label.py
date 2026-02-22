import time
import networkx as nx
import os
import subprocess
from src.graph_types import GraphType


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


def collect_labelg(labels: list[bytes]) -> list[str]:
    """
    Collect the canonical label for all the labels using only one labelg process, instead of
    spawning a process for each label.
    Expect the labelg executable to exists in the root directory.
    Pass the labels list with each label on its own line, labelg will maintain the order in the
    output results.
    """
    if not labels:
        return []

    start_time = time.perf_counter()
    label_g = "./labelg"
    if os.path.isfile(label_g):
        os.chmod(label_g, 0o755)
    else:
        raise RuntimeError("labelg executable not found")

    str_labels = map(lambda b: b.decode("ascii"), labels)
    labelg_input = "\n".join(str_labels)
    result = subprocess.run(
        [label_g],
        input=labelg_input,
        text=True,
        capture_output=True,
    )

    # if subprocess runs correctly, return the output lines
    if result.returncode != 0:
        raise RuntimeError(f"labelg subprocess failed with return code: {result.returncode}")

    result_labels = result.stdout.rstrip().split("\n")
    print(f"Time to label {len(labels)} labels: {(time.perf_counter() - start_time):.6f} s")
    return result_labels


def basic_graph_label(nx_graph: nx.Graph, subgraph_nodes: list, graph_type: GraphType) -> bytes:
    """
    Label a graph in either graph6 (undirected) or digraph6 (directed) format.
    """
    if graph_type == GraphType.UNDIRECTED:
        return g6(nx_graph, subgraph_nodes)
    return d6(nx_graph, subgraph_nodes)
