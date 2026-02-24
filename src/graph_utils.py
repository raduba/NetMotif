"""
Graph Class

This class is responsible for graph generation, visualization, and\
    rendering using NetworkX and Pyvis.

"""

from typing import List
import networkx as nx
import os
import io
import streamlit as st
import streamlit.components.v1 as components
from streamlit.runtime.uploaded_file_manager import UploadedFile
from pyvis.network import Network
from src.graph_types import GraphType


class Graph:
    def __init__(self, graph_type, input):
        self.graph_type = graph_type
        self.file = input
        self.G = None

        # build graph
        if graph_type == GraphType.UNDIRECTED:
            self.G = nx.Graph()
        elif graph_type == GraphType.DIRECTED:
            self.G = nx.DiGraph()

        # if input is Graph or DiGraph handle differently
        if isinstance(input, UploadedFile) or isinstance(input, io.BytesIO):
            if input is not None:
                bytes_data = io.StringIO(input.getvalue().decode("utf-8"))
                data = bytes_data.readlines()
                for line in data:
                    nodes = line.strip().split()
                    if len(nodes) == 2:
                        self.G.add_edge(nodes[0], nodes[1])
        elif isinstance(input, str):
            self.read_file(input)
        else:
            self.G = input

    def read_file(self, file_directory):
        with open(file_directory, "r") as f:
            file_content_edges = f.readlines()
            for edge in file_content_edges:
                nodes = edge.strip().split()
                if len(nodes) == 2:
                    self.G.add_edge(nodes[0], nodes[1])

    def get_graph_properties(self):
        if self.G is None:
            return {}

        return {
            "Number of nodes": self.G.number_of_nodes(),
            "Edges": list(self.G.edges()),
            "Number of edges": self.G.number_of_edges(),
            "Weight": self.G.size(),
        }

    """
    def draw_random_graphs(self, number_of_graphs) -> list["Graph"]:
        random_graphs = rg.generate_random_graphs(self, number_of_graphs)
        for graph in random_graphs:
            graph.draw_graph()
        return random_graphs
    """

    def draw_graph(self, output_file_name="nx.html"):
        output_dir = "drawings"
        if self.graph_type == GraphType.DIRECTED:
            nt = Network(directed=True)
        else:
            nt = Network()
        nt.from_nx(self.G)
        nt.toggle_physics(True)  # add physic to graph
        nt.toggle_hide_edges_on_drag(True)
        # nt.show_buttons(filter_=["physics"])

        # Render the graph to an HTML file
        # file_name = os.path.join(output_dir, output_file_name)

        # make sure output folder for the drawings exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # nt.write_html(file_name, open_browser=False)
        # with open(file_name, "r") as f:
        #     html = f.read()

        # Render the graph to a string
        html = nt.generate_html()
        components.html(html, height=700, scrolling=True)
