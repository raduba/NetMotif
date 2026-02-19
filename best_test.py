from src.graph_utils import Graph
from src.graph_types import GraphType
import src.motif_statistics as stat
import src.random_graph as rg
import streamlit as st
from io import BytesIO

print("running stats table test")
best_graph = Graph(GraphType.DIRECTED, './data/bestTest.txt', 3)
print(best_graph.subgraph_list_enumerated)
random_graphs = rg.generate_random_graphs(best_graph, 10)
# make a table of data for each label
table = stat.processStatistics(best_graph, random_graphs)
print(table)