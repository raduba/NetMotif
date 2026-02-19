import time
from typing import List
import igraph as ig
import streamlit as st
from src.subgraph import Subgraph
from src.graph_types import GraphType
import src.label as lb


class ESU:
    def __init__(self, G: ig.Graph, size: int, graph_type: GraphType):
        """
        Enumerates all unique subgraphs of a given motif size from the input
                graph using the ESU algorithm.
        """
        self.G = G
        self.size = size
        self.graph_type = graph_type
        # (ig.Graph, node_ids)[]
        self.subgraph_list: List[tuple[ig.Graph, list[int]]] = []
        self.Subgraph_list: List[Subgraph] = []
        self.node_visited = set()
        self.nodes = list(range(self.G.vcount()))

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
        print(f"enumerated {len(self.subgraph_list)} in {(esu_time - start_time):.6f} seconds")
        st.write(
            f"ESU.esu time to find {len(self.subgraph_list)} subgraphs: {(esu_time - start_time):.6f} seconds"
        )

        # Progress bar for labeling subgraphs
        progress_text = "Labeling algorithm in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)

        labeling_start_time = time.perf_counter()

        # apply the d6 labels in parallel
        basic_labeling_start_time = time.perf_counter()
        subgraphs = [Subgraph(graph_type=self.graph_type, input=sub, node_ids=nodes) for sub, nodes in self.subgraph_list]
        subgraphs_params = [(sub, self.graph_type) for sub, _ in self.subgraph_list]
        basic_labels = lb.calculate_basic_labels(subgraphs_params)
        for s, basic_label in zip(subgraphs, basic_labels):
            s.basic_label = basic_label
        st.write(
            f"ESU.basic_labeling_time time for {len(self.subgraph_list)} subgraphs: {(time.perf_counter() - basic_labeling_start_time):.6f} seconds"
        )

        progress_text = "Canonical label translation in progress. Please wait."
        my_bar.progress(0, text=progress_text)

        labelg_start_time = time.perf_counter()
        labelg_input = [sub.basic_label for sub in subgraphs]
        labels = lb.collect_labelg(labelg_input)
        for i, label in enumerate(labels):
            subgraphs[i].set_label(label)
        st.write(f"ESU.labelg time: {(time.perf_counter() - labelg_start_time):.6f} seconds")

        self.Subgraph_list = subgraphs

        st.write(f"ESU.labeling time: {(time.perf_counter() - labeling_start_time):.6f} seconds")

        my_bar.empty()

    def esu_recursive_helper(
        self, size: int, neighbors: set[int], node_list: list[int], subgraph_list: list[tuple[ig.Graph, list[int]]], nodes_visited: set[int]
    ):
        if size == 1:
            subgraph_list.append((self.G.induced_subgraph(node_list), list(node_list)))
            return

        if not neighbors:
            return

        for node in neighbors:
            node_list.append(node)
            nodes_visited.add(node)

            # Efficiently get next neighbors
            next_neighbors = {n for n in neighbors if n not in nodes_visited}
            for neighbor in self.G.neighbors(node, mode=ig.OUT):
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
        return [n for n in self.G.neighbors(node, mode=ig.OUT) if n > node]

    def get_subgraph_list(self):
        return self.Subgraph_list

    def number_of_subgraphs(self):
        return len(self.Subgraph_list)
