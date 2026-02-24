import io
from pathlib import Path
import networkx as nx
from src.graph_types import GraphType
from src.graph_with_subgraph import GraphWithSubgraph

DATA_DIR = Path(__file__).parent.parent / "data"


def compute_label_frequencies(
    input: str | io.BytesIO | nx.Graph | nx.DiGraph,
    size: int,
    graph_type: GraphType = GraphType.UNDIRECTED,
) -> dict[str, float]:
    """
    Runs ESU + canonicalization and returns {canonical_label: percent frequency}
    for every subgraph of the given size.

    :param input: file path or data buffer or nx graph
    :param size: motif size
    :param graph_type: GraphType.UNDIRECTED or GraphType.DIRECTED
    """

    g = GraphWithSubgraph(graph_type, input, size)
    return get_label_frequencies(g)


def get_label_frequencies(graph: GraphWithSubgraph) -> dict[str, float]:
    """
    Gets the label frequencies ({canonical_label: percent frequency}) for a graph
    that has already had ESU and canonicalization run on it.

    :param graph: the graph to extract frequencies from
    """

    # Use percentage frequencies, since that's what the
    # website returns, so it's easier to compare.
    total_count = float(sum(graph.subgraph_list_enumerated.values()))
    return {
        subgraph.get_label(): 100 * float(count) / total_count
        for subgraph, count in graph.subgraph_list_enumerated.items()
    }
