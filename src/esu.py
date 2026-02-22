import time
from typing import Dict, Generator, List
import networkx as nx
from src.subgraph import Subgraph
from src.graph_types import GraphType
import src.label as lb


class ESU:
    def __init__(self, G: nx.Graph, size: int, graph_type: GraphType, progress_update=None):
        """
        Enumerates all unique subgraphs of a given motif size from the input
                graph using the ESU algorithm.
        """
        self.G = G
        self.G_undirected = (
            G if graph_type == GraphType.UNDIRECTED
            else G.to_undirected(as_view=True)
        )
        self.size = size
        self.graph_type = graph_type
        self._enumerate_subgraphs: Dict[Subgraph, int] = {}
        self.nodes = list(self.G.nodes())
        self._node_indices = {n: i for i, n in enumerate(self.nodes)}

        # basic label -> [count, subgraph_nodes_list]
        subgraph_count: dict[bytes, List] = {}
        self._total_subgraphs = 0

        start_time = time.perf_counter()

        for sg_nodes in self.esu():
            self._total_subgraphs += 1
            g6 = lb.basic_graph_label(self.G, sg_nodes, self.graph_type)

            if g6 in subgraph_count:
                subgraph_count[g6][0] += 1
            else:
                # keep one subgraph / g6 so we can show it in the UI
                subgraph_count[g6] = [1, sg_nodes]

        esu_time = time.perf_counter()
        print(f"enumerated {self._total_subgraphs} in {(esu_time - start_time):.6f} seconds")

        # Progress bar for labeling subgraphs
        if progress_update is not None:
            progress_update("Labeling algorithm in progress. Please wait.")

        labelg_start_time = time.perf_counter()

        # canonical label -> [count, Subgraph]
        enumerate_subgraphs: Dict[str, List] = {}
        subgraph_labels = list(subgraph_count.keys())
        canonical_labels = lb.collect_labelg(subgraph_labels)

        print(f"ESU.labelg time: {(time.perf_counter() - labelg_start_time):.6f} seconds")

        for matched_label, canonical_label in zip(subgraph_labels, canonical_labels):
            matched_count, matched_subgraph_nodes = subgraph_count[matched_label]
            if canonical_label in enumerate_subgraphs:
                enumerate_subgraphs[canonical_label][0] += matched_count
            else:
                nx_subgraph = self.G.subgraph(matched_subgraph_nodes)
                s = Subgraph(graph_type=self.graph_type, input=nx_subgraph, label=canonical_label)
                enumerate_subgraphs[canonical_label] = [matched_count, s]

        self._enumerate_subgraphs = {s: count for count, s in enumerate_subgraphs.values()}

    def esu(self) -> Generator[list, None, None]:
        """
        Return subgraphs nodes in a generator so that we don't run out of memory for k > 5,
        when we can have tens of millions of subgraphs on 1000 nodes and edges graphs
        """
        for node in self.nodes:
            node_list = [node]
            node_visited = {node}
            node_index = self._node_indices[node]
            yield from self._esu_helper(
                self.size,
                set(self.get_right_neighbors(node)),
                node_list,
                node_visited,
                node_index
            )

    def _esu_helper(
        self, size: int, neighbors: set, node_list: list, nodes_visited: set, root_index: int
    ) -> Generator[list, None, None]:
        if size == 1:
            yield node_list[:]
            return

        if not neighbors:
            return

        for node in neighbors:
            node_list.append(node)
            nodes_visited.add(node)

            # Efficiently get next neighbors
            new_neighbors = {
                n for n in self.G_undirected.neighbors(node) if self._node_indices[n] > root_index
            }
            next_neighbors = neighbors.union(new_neighbors)
            next_neighbors.difference_update(nodes_visited)

            yield from self._esu_helper(size - 1, next_neighbors, node_list, nodes_visited, root_index)

            node_list.pop()

        # Ensure we discard nodes from visited set after recursion
        nodes_visited.difference_update(neighbors)

    def get_right_neighbors(self, node):
        # Retrieve neighbors that are "right" of the given node in the graph's index order
        node_index_in_g = self._node_indices[node]
        return (
            w for w in self.G_undirected.neighbors(node)
            if self._node_indices[w] > node_index_in_g
        )

    def get_enumerated_subgraphs(self) -> Dict[Subgraph, int]:
        return self._enumerate_subgraphs

    def number_of_subgraphs(self):
        return self._total_subgraphs
