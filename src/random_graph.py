import streamlit as st
from src.motif_search import random_esu
from src.graph_with_subgraph import GraphWithSubgraph


def generate_random_graphs(mimicked_graph: GraphWithSubgraph,
                           number_of_graphs) -> list[GraphWithSubgraph]:
    progress_text = "Random graph generation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)

    def _progress(i):
        my_bar.progress(i / number_of_graphs, text=progress_text)
        if i == number_of_graphs:
            my_bar.empty()

    esu_results = random_esu(
        G_mimicked=mimicked_graph.G,
        motif_size=mimicked_graph.motif_size,
        graph_type=mimicked_graph.graph_type,
        number_of_graphs=number_of_graphs,
        complete_callback=_progress
    )

    return [
        GraphWithSubgraph(
            graph_type=mimicked_graph.graph_type,
            input=esu.G,
            motif_size=mimicked_graph.motif_size,
            esu=esu
        ) for esu in esu_results
    ]
