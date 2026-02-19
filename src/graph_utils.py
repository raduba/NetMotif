"""
Graph Class

This class is responsible for graph generation, visualization, and\
    rendering using igraph and Pyvis.

"""

import igraph as ig
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
        # vertex ID -> node label
        self.node_list = []

        if isinstance(input, UploadedFile) or isinstance(input, io.BytesIO):
            if input is not None:
                lines = io.StringIO(input.getvalue().decode("utf-8")).readlines()
                self.parse_graph(lines)
        elif isinstance(input, str):
            self.read_file(input)
        elif isinstance(input, ig.Graph):
            self.G = input
            self.node_list = list(range(input.vcount()))

    def read_file(self, file_directory):
        with open(file_directory, 'r') as f:
            self.parse_graph(f.readlines())


    # Parses a graph from the given file lines into this object.
    def parse_graph(self, lines):
        self.node_list = []

        # label -> vertex ID
        node_map = {}
        # (from, to)[]
        edges = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                src, dst = parts
                if src not in node_map:
                    node_map[src] = len(self.node_list)
                    self.node_list.append(src)
                if dst not in node_map:
                    node_map[dst] = len(self.node_list)
                    self.node_list.append(dst)

                edges.append((node_map[src], node_map[dst]))

        self.G = ig.Graph(n=len(self.node_list), edges=edges, directed=(self.graph_type == GraphType.DIRECTED))

    def get_graph_properties(self):
        if self.G is None:
            return {}

        return {
            "Number of nodes": self.G.vcount(),
            "Edges": self.G.get_edgelist(),
            "Number of edges": self.G.ecount(),
            "Weight": self.G.ecount(),
        }

    '''
    def draw_random_graphs(self, number_of_graphs) -> list["Graph"]:
        random_graphs = rg.generate_random_graphs(self, number_of_graphs)
        for graph in random_graphs:
            graph.draw_graph()
        return random_graphs
    '''

    def draw_graph(self, output_file_name = "nx.html"):
        output_dir = "drawings"
        if self.graph_type == GraphType.DIRECTED:
            nt = Network(directed=True)
        else:
            nt = Network()
        nt.from_nx(ig.Graph.to_networkx(self.G))
        nt.toggle_physics(True)  # add physic to graph
        nt.toggle_hide_edges_on_drag(True)
        #nt.show_buttons(filter_=["physics"])

        # Render the graph to an HTML file
        file_name = os.path.join(output_dir, output_file_name)

        # make sure output folder for the drawings exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        nt.write_html(file_name, open_browser=False)
        with open(file_name, "r") as f:
            html = f.read()

        components.html(html, height=700, scrolling=True)