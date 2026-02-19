import time
from typing import Dict, Generator, List
import networkx as nx
import streamlit as st
from src.subgraph import Subgraph
from src.graph_types import GraphType
import src.label as lb


class ESU:
    def __init__(self, G: nx.Graph, size: int, graph_type: GraphType):
        """
        Enumerates all unique subgraphs of a given motif size from the input
                graph using the ESU algorithm.
        """
        self.G = G
        self.size = size
        self.graph_type = graph_type
        # We do not need to persist the complete list of subgraphs, refactor the UI and stats
        # components so that they calls get_total_subgraphs() instead
        # TODO: update the code to handle SubgraphProfile and SubgraphCollection cases, when
        # we need to save all the subgraphs in a file
        self._subgraph_list: List[Subgraph] = []
        self._enumerate_subgraphs: Dict[Subgraph, int] = {}
        self.nodes = list(self.G.nodes())
        self.number_of_conversions = 0

        subgraph_count: dict[str, List] = {}
        self._total_subgraphs = 0

        # Progress bar for subgraph enumeration
        progress_text = "ESU algorithm in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)
        start_time = time.perf_counter()

        for sg in self.esu():
            self._total_subgraphs += 1
            g6 = lb.get_basic_graph_label(sg, self.graph_type)

            if g6 in subgraph_count:
                subgraph_count[g6][0] += 1
            else:
                # keep one subgraph / g6 so we can show it in the UI
                s = Subgraph(graph_type=self.graph_type, input=sg, basic_label=g6)
                subgraph_count[g6] = [1, s]
                # subgraph_list keeps the list of unique subgraphs using non-canonical labels,
                # so only one subgraphs will be stored / g6 label
                # not needed and downstream code should be rafactored so that it does not use it
                self._subgraph_list.append(s)

        my_bar.empty()

        esu_time = time.perf_counter()
        print(f"enumerated {self._total_subgraphs} in {(esu_time - start_time):.6f} seconds")
        st.write(
            f"ESU.esu time to find {self._total_subgraphs} subgraphs: {(esu_time - start_time):.6f} seconds"
        )

        # Progress bar for labeling subgraphs
        progress_text = "Labeling algorithm in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)

        progress_text = "Canonical label translation in progress. Please wait."
        my_bar.progress(0, text=progress_text)

        labelg_start_time = time.perf_counter()

        enumerate_subgraphs: Dict[Subgraph, int] = {}
        subgraph_labels = list(subgraph_count.keys())
        canonical_labels = lb.collect_labelg(subgraph_labels)

        st.write(f"ESU.labelg time: {(time.perf_counter() - labelg_start_time):.6f} seconds")

        for matched_label, canonical_label in zip(subgraph_labels, canonical_labels):
            matched_count, matched_subgraph = subgraph_count[matched_label]
            matched_subgraph.set_label(canonical_label)
            # matched_subgraph Subgraph is hashed by the canonical_label
            if matched_subgraph in enumerate_subgraphs:
                enumerate_subgraphs[matched_subgraph] += matched_count
            else:
                enumerate_subgraphs[matched_subgraph] = matched_count

        self._enumerate_subgraphs = enumerate_subgraphs

        my_bar.empty()

    def esu(self) -> Generator[nx.Graph]:
        """
        Return subgraphs in a generator so that we don't run out of memory for k > 5, when we can
        have tens of millions of subgraphs on 1000 nodes and edges graphs
        """
        node_visited = set()
        for node in self.nodes:
            node_list = [node]
            node_visited.add(node)
            yield from self._esu_helper(
                self.size,
                set(self.get_right_neighbors(node)),
                node_list,
                node_visited,
            )

    def _esu_helper(
        self, size: int, neighbors: set, node_list: list, nodes_visited: set
    ) -> Generator[nx.Graph]:
        if size == 1:
            yield self.G.subgraph(node_list)
            return

        if not neighbors:
            return

        for node in neighbors:
            node_list.append(node)
            nodes_visited.add(node)

            # Efficiently get next neighbors
            next_neighbors = {n for n in neighbors if n not in nodes_visited}
            for neighbor in nx.neighbors(self.G, node):
                if neighbor not in nodes_visited:
                    next_neighbors.add(neighbor)

            yield from self._esu_helper(size - 1, next_neighbors, node_list, nodes_visited)

            node_list.pop()

        # Ensure we discard nodes from visited set after recursion
        nodes_visited.difference_update(neighbors)

    def get_right_neighbors(self, node):
        # Retrieve neighbors that are "right" of the given node in the graph's index order
        node_index_in_g = self.nodes.index(node)
        return (n for i, n in enumerate(self.G) if i > node_index_in_g and self.G.has_edge(node, n))

    def get_subgraph_list(self):
        return self._subgraph_list

    def get_enumerated_subgraphs(self):
        return self._enumerate_subgraphs

    def number_of_subgraphs(self):
        return self._total_subgraphs
