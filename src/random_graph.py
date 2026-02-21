import networkx as nx
from src.graph_utils import Graph
from src.graph_with_subgraph import GraphWithSubgraph
from src.graph_types import GraphType
from src.progress import ProgressUpdate, Logger, ProgressState

def generate_random_graphs(mimicked_graph: Graph, motif_size: int, number_of_graphs, progress: ProgressUpdate = None, logger: Logger = None) -> list[GraphWithSubgraph]:
    if progress:
        progress(ProgressState.RANDOM, 0)

    random_graphs: list[GraphWithSubgraph] = []
    for i in range(number_of_graphs):
        random_graphs.append(generate_random_graph(mimicked_graph, motif_size, progress, logger))
        if progress:
            progress(ProgressState.RANDOM, float(i + 1)/float(number_of_graphs))

    if progress:
        progress(ProgressState.RANDOM, 1)

    return random_graphs

def generate_random_graph(mimicked_graph: Graph, motif_size: int, progress: ProgressUpdate = None, logger: Logger = None, seed = None):
    if mimicked_graph.graph_type == GraphType.UNDIRECTED:
            degree_sequence = [d for _, d in mimicked_graph.G.degree()]
            random_nx_graph = nx.Graph(nx.configuration_model(degree_sequence, seed=seed))
    elif mimicked_graph.graph_type == GraphType.DIRECTED:
        in_degree_sequence = [d for _, d in mimicked_graph.G.in_degree()]
        out_degree_sequence = [d for _, d in mimicked_graph.G.out_degree()]
        random_nx_graph = nx.DiGraph(
            nx.directed_configuration_model(
                in_degree_sequence, out_degree_sequence, seed=seed
            )
        )
    random_nx_graph.remove_edges_from(nx.selfloop_edges(random_nx_graph))
    random_graph = GraphWithSubgraph(
        graph_type=mimicked_graph.graph_type,
        input=random_nx_graph,
        motif_size=motif_size,
        progress=progress,
        logger=logger
    )
    return random_graph