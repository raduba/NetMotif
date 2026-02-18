import time
from typing import List
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
        self.subgraph_list: List[nx.Graph] = []
        self.Subgraph_list: List[Subgraph] = []
        self.node_visited = set()
        self.label_conversion_map = {}
        self.nodes = list(self.G.nodes())
        self.number_of_conversions = 0

        # Progress bar for subgraph enumeration
        progress_text = "ESU algorithm in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)
        total_nodes = len(self.nodes)
        start_time = time.perf_counter()

        for i, node in enumerate(self.nodes):
            node_list = [node]
            self.node_visited.add(node)
            self.esu_recursive_helper(
                self.size,
                set(self.get_right_neighbors(node)),
                node_list,
                self.subgraph_list,
                self.node_visited,
            )
            my_bar.progress((i + 1) / total_nodes, text=progress_text)
        my_bar.empty()

        esu_time = time.perf_counter()
        st.write(
            f"ESU.esu time to find {len(self.subgraph_list)} subgraphs: {(esu_time - start_time):.6f} seconds"
        )

        # Progress bar for labeling subgraphs
        progress_text = "Labeling algorithm in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)

        labeling_start_time = time.perf_counter()

        for i, subgraph in enumerate(self.subgraph_list):
            sub = Subgraph(graph_type=self.graph_type, input=subgraph)
            d6 = lb.get_basic_graph_label(sub.G, self.graph_type)

            if d6 not in self.label_conversion_map:
                self.number_of_conversions += 1
                g6 = lb.get_graph_label(
                    sub.G, self.graph_type
                )  # Expensive operation, minimize calls!
                self.label_conversion_map[d6] = g6
                sub.set_label(g6)
            else:
                sub.set_label(self.label_conversion_map[d6])

            self.Subgraph_list.append(sub)
            my_bar.progress((i + 1) / len(self.subgraph_list), text=progress_text)

        st.write(f"ESU.labeling time: {(time.perf_counter() - labeling_start_time):.6f} seconds")

        my_bar.empty()

    def esu_recursive_helper(
        self, size: int, neighbors: set, node_list: list, subgraph_list: list, nodes_visited: set
    ):
        if size == 1:
            subgraph_list.append(self.G.subgraph(node_list))
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

            self.esu_recursive_helper(
                size - 1, next_neighbors, node_list, subgraph_list, nodes_visited
            )

            node_list.pop()

        # Ensure we discard nodes from visited set after recursion
        nodes_visited.difference_update(neighbors)

    def get_right_neighbors(self, node):
        # Retrieve neighbors that are "right" of the given node in the graph's index order
        nodes_list = list(self.G.nodes)
        node_index_in_g = nodes_list.index(node)
        return (n for i, n in enumerate(self.G) if i > node_index_in_g and self.G.has_edge(node, n))

    def get_subgraph_list(self):
        return self.Subgraph_list

    def number_of_subgraphs(self):
        return len(self.Subgraph_list)
