from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List

import networkx as nx
from src.esu import ESU
from src.graph_types import GraphType


def _randomized_esu(G_mimicked: nx.Graph, motif_size: int,
                    graph_type: GraphType, seed: int | None = None) -> ESU:
    """
    Worker function that runs ESU algorithm on a process worker, so the random
    graphs execution can be parallelized.
    """
    if graph_type == GraphType.UNDIRECTED:
        degree_sequence = [d for _, d in G_mimicked.degree()]
        G_random = nx.Graph(nx.configuration_model(degree_sequence, seed=seed))
    else:
        in_degrees = [d for _, d in G_mimicked.in_degree()]
        out_degrees = [d for _, d in G_mimicked.out_degree()]
        G_random = nx.DiGraph(
            nx.directed_configuration_model(in_degrees, out_degrees, seed=seed)
            )
    G_random.remove_edges_from(nx.selfloop_edges(G_random))
    return ESU(G_random, motif_size, graph_type, progress_update=None)


def random_esu(G_mimicked: nx.Graph,
               motif_size: int,
               graph_type: GraphType,
               number_of_graphs: int,
               complete_callback,
               seed: int | None = None) -> List[ESU]:
    """
    Runs the ESU algorithm on all available CPUs in parallel.
    Returns a list of ESU instances that can be used to construct GraphWithSubgraph
    for the UI and for the statistics calculation.
    """
    task_params = [
        (G_mimicked, motif_size, graph_type, seed) for _ in range(number_of_graphs)
    ]
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(_randomized_esu, *t) for t in task_params]
        results = []
        completed = 0
        for future in as_completed(futures):
            try:
                results.append(future.result())
                completed += 1
                complete_callback(completed)
            except Exception as e:
                print(f"Failed to run ESU for worker: {e}")
        return results
