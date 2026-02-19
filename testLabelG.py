from src.graph_utils import Graph
from src.graph_types import GraphType
import src.motif_statistics as stat
import src.random_graph as rg
import streamlit as st
from io import BytesIO

print("running labelG test without streamlit")
basic_graph = Graph(GraphType.UNDIRECTED, './data/basicTest.txt', 3)
print(basic_graph.subgraph_list_enumerated)
random_graphs = rg.generate_random_graphs(basic_graph, 10)
# make a table of data for each label
table = stat.processStatistics(basic_graph, random_graphs)
print(table)