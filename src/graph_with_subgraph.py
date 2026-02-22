from typing import Dict
import networkx as nx
import os
import streamlit as st
from src.graph_utils import Graph
from src.subgraph import Subgraph
from src.esu import ESU


class GraphWithSubgraph(Graph):
    def __init__(self, graph_type, input, motif_size, esu=None):
        # instantiation of Graph object
        super().__init__(graph_type, input)
        # TODO: reimplement and subgraph_collection so that we don;t need to keep the list
        #  of all iterated subgraphs
        # self.subgraph_list: list[Subgraph] = []
        # dictionary of subgraph enumeration (Subgraph -> #)
        self.subgraph_list_enumerated: Dict[Subgraph, int] = {}
        # number of nodes in subgraphs
        self.motif_size: int = motif_size
        # remove self loops
        self.G.remove_edges_from(nx.selfloop_edges(self.G))

        # esu object for esu algorithm
        if esu is None:
            # creating Subgraph list and dict
            self.my_bar = st.progress(0, text="ESU algorithm in progress. Please wait.")
            self.esu = self.runESU(motif_size, graph_type)
            self.my_bar.empty()
        else:
            # use the result from an already run esu
            self.esu = esu

        self.total_subgraphs = self.esu.number_of_subgraphs()

        # convert esu results to a Subgraph that can be rendered
        for canonical_label, (count, subgraph_nodes) in self.esu.get_enumerated_subgraphs().items():
            nx_subgraph = self.G.subgraph(subgraph_nodes)
            s = Subgraph(graph_type=self.graph_type, input=nx_subgraph, label=canonical_label)
            self.subgraph_list_enumerated[s] = count

    def runESU(self, motif_size, graph_type):
        # produce list of subgraphs
        # Progress update for subgraph enumeration
        def _progress_update(text):
            self.my_bar.empty()
            self.my_bar = st.progress(0, text=text)
            self.my_bar.progress(0, text=text)

        return ESU(self.G, motif_size, graph_type, _progress_update)

    def draw_subgraph(self):
        output_dir = "drawings/subgraphs"  # output directory
        # make sure output folder for the drawings exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for i, subgraph in enumerate(self.subgraph_list_enumerated.keys()):
            st.markdown(f"### Subgraph {subgraph.get_label()}")
            subgraph.draw_graph("nx_subgraph_{i}.html")
        return

    def get_graph_properties(self):
        simple_properties = super().get_graph_properties()
        if simple_properties is None:
            return None

        simple_properties.update(
            {
                "Number of subgraphs": self.total_subgraphs,
            }
        )

        return simple_properties

    def generate_nemo_count(self):
        # do nothing
        return

    # @st.cache_data
    def generate_subgraph_profile(self):
        # TODO: reimplement it without keeping the whole list of subgraphs
        raise ValueError("Not implemented")
        output_dir = "out"
        subgraph_profile_output = os.path.join(output_dir, "subgraph_profile.txt")

        # Ensure output folder exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # label-node count dictionary
        nodes_dictionary = {}

        # iterate over subgraphs
        # TODO: update this so that we don't need to keep the subgraphs list
        for subgraph in self.subgraph_list:
            label = subgraph.get_label()
            # if label not accounted for
            if label not in nodes_dictionary:
                # fill in all node count as 0 for label
                nodes_dictionary[label] = {}
                for node in self.G:
                    nodes_dictionary[label][node] = 0
            # for every node in the subgraph add 1 to its label-node count
            for node in subgraph.G.nodes:
                nodes_dictionary[label][node] += 1

        # Write into file
        with open(subgraph_profile_output, "w") as file:
            top_row = f"{'Nodes':<10}"  # top row for graph labels
            for key in nodes_dictionary:
                top_row += f"{key.strip():<10}"  # strip new line from label
            top_row += "\n"  # make space for the nodes and their count
            file.write(top_row)
            # each nodes count in its associated graph
            for node in self.G:
                line = f"{node:<10}"
                for key in nodes_dictionary:
                    line += f"{nodes_dictionary[key][node]:<10}"
                line += "\n"
                file.writelines(line)

        # Display download button for file
        with open(subgraph_profile_output, "r") as file:
            return st.download_button(
                label="Download subgraph profile",
                data=file,
                file_name="subgraph_profile.txt",
            )

    # @st.cache_data
    def generate_subgraph_collection(self):
        # TODO: reimplement it without keeping the whole list of subgraphs
        raise ValueError("Not implemented")
        output_dir = "out"
        subgraph_collection_output = os.path.join(output_dir, "subgraph_collection.txt")

        # Ensure output folder exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write into file
        with open(subgraph_collection_output, "w") as file:
            for subgraph in self.subgraph_list:
                nodes = subgraph.G.nodes()
                line = ""
                line += subgraph.get_label() + "[" + ", ".join([str(x) for x in nodes]) + "] \n"
                file.write(line)

        # Display download button for file
        with open(subgraph_collection_output, "r") as file:
            return st.download_button(
                label="Download subgraph collection",
                data=file,
                file_name="subgraph_collection.txt",
            )
