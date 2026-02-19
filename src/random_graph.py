import igraph as ig
import streamlit as st
from src.graph_with_subgraph import GraphWithSubgraph
from src.graph_types import GraphType

def generate_random_graphs(mimicked_graph: GraphWithSubgraph, number_of_graphs) -> list[GraphWithSubgraph]:
    progress_text = "Random graph generation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)
    random_graphs: list[GraphWithSubgraph] = []
    for i in range(number_of_graphs):
        random_graphs.append(generate_random_graph(mimicked_graph))
        my_bar.progress(i/st.session_state['number_of_random_graphs'], text=progress_text)
    my_bar.empty()
    return random_graphs

def generate_random_graph(mimicked_graph: GraphWithSubgraph):
    if mimicked_graph.graph_type == GraphType.UNDIRECTED:
        random_graph = ig.Graph.Degree_Sequence(mimicked_graph.G.degree(), method="configuration")
    elif mimicked_graph.graph_type == GraphType.DIRECTED:
        random_graph = ig.Graph.Degree_Sequence(
            mimicked_graph.G.outdegree(),
            mimicked_graph.G.indegree(),
            method="configuration",
        )
    random_graph.simplify()
    return GraphWithSubgraph(
        graph_type=mimicked_graph.graph_type,
        input=random_graph,
        motif_size=mimicked_graph.motif_size,
    )
