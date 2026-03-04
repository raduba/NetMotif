import random
import time
from typing import Dict, Generator, List, Tuple, Callable
import networkx as nx
from src.graph_types import GraphType
import src.label as lb
from src.label import AsyncLabelg


class ESU:
    def __init__(
        self,
        G: nx.Graph,
        size: int,
        graph_type: GraphType,
        label_callback: Callable[[str, list], None] = None,
        probabilities: List[float] | None = None,
    ):
        """
        Enumerates the unique subgraphs of a given motif size from the input graph using the ESU
        algorithm. The implementation is based on the algorithm as described in the
        'A Faster Algorithm for Detecting Network Motifs' paper by Wernicke, which runs full
        subgraph enumeration when all probabilities are 1.0 and the sampling method when nodes are
        explored with the configured tree level probability.

        When probabilities is None, returns the full subgraph enumeration.
        """
        if probabilities is not None:
            if len(probabilities) != size:
                raise ValueError("probabilities must have size equal to motif size")

            if any(p <= 0.0 or p > 1.0 for p in probabilities):
                raise ValueError("probabilities must have 0.0 < p <= 1.0")

        self.G = G
        self.G_undirected = (
            G if graph_type == GraphType.UNDIRECTED else G.to_undirected(as_view=True)
        )
        self.size = size
        self.graph_type = graph_type
        # canonical label -> (count, subgraph_nodes)
        self._enumerate_subgraphs: Dict[str, Tuple[int, List]] = {}
        self.nodes = list(self.G.nodes())
        self._node_indices = {n: i for i, n in enumerate(self.nodes)}
        self._total_subgraphs = 0
        self._probabilities = probabilities

        # Canonical label -> [number of subgraphs, reference subgraph nodes]
        enumerate_subgraphs: Dict[str, List[int | List]] = {}

        start_time = time.perf_counter()

        # This takes in a node list
        def on_label(canonical_label: str, data: List):
            if canonical_label in enumerate_subgraphs:
                enumerate_subgraphs[canonical_label][0] += 1
            else:
                enumerate_subgraphs[canonical_label] = [1, data]

            if label_callback:
                label_callback(canonical_label, data)

        labelg = AsyncLabelg(on_label)

        for sg_nodes in self._esu():
            self._total_subgraphs += 1
            g6 = lb.basic_graph_label(self.G, sg_nodes, self.graph_type)
            labelg.label(g6, sg_nodes)

        labelg.finish()

        esu_time = time.perf_counter()
        print(f"enumerated {self._total_subgraphs} in {(esu_time - start_time):.6f} seconds")

        for label, (count, subgraph_nodes) in enumerate_subgraphs.items():
            self._enumerate_subgraphs[label] = count, subgraph_nodes

    def _esu(self) -> Generator[list, None, None]:
        """
        Return subgraphs nodes in a generator so that we don't run out of memory for k > 5,
        when we can have tens of millions of subgraphs on 1000 nodes and edges graphs.
        Set all probabilities of selecting a node at a level to 1.0 for full ESU.
        The level starts from 0 for the root nodes, and increases by 1 for each _esu_helper call.
        When probability is less than 1.0, the sampling method is used and nodes are explored with
        the probability given by level.
        """
        for node in self.nodes:
            if self._probabilities is not None and random.random() >= self._probabilities[0]:
                continue
            node_list = [node]
            node_visited = {node}
            node_index = self._node_indices[node]
            yield from self._esu_helper(
                self.size, set(self.get_right_neighbors(node)), node_list, node_visited, node_index
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
            # Subgraph sampling, randomly exclude branches for faster computation.
            # We have to append to nodes_visited first, before skipping the branch.
            # That's because nodes_visited functions as the ESU neighbors of neighbors check,
            # ensuring we only enumerate each subgraph once.
            # If we conditionally append to it, then we'll end up changing the graph.
            nodes_visited.add(node)
            if (
                self._probabilities is not None
                and random.random() >= self._probabilities[self.size - size + 1]
            ):
                continue

            node_list.append(node)

            # Efficiently get next neighbors
            new_neighbors = {
                n for n in self.G_undirected.neighbors(node) if self._node_indices[n] > root_index
            }
            next_neighbors = neighbors.union(new_neighbors)
            next_neighbors.difference_update(nodes_visited)

            yield from self._esu_helper(
                size - 1, next_neighbors, node_list, nodes_visited, root_index
            )

            node_list.pop()

        # Ensure we discard nodes from visited set after recursion
        nodes_visited.difference_update(neighbors)

    def get_right_neighbors(self, node):
        # Retrieve neighbors that are "right" of the given node in the graph's index order
        node_index_in_g = self._node_indices[node]
        return (
            w for w in self.G_undirected.neighbors(node) if self._node_indices[w] > node_index_in_g
        )

    def get_enumerated_subgraphs(self) -> Dict[str, Tuple[int, List]]:
        """Returns the canonical_label -> (count, subgraph_nodes) mapping"""
        return self._enumerate_subgraphs

    def number_of_subgraphs(self):
        return self._total_subgraphs
