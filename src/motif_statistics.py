from src.graph_with_subgraph import GraphWithSubgraph
from src.subgraph import Subgraph
import math
import scipy.stats
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def draw_statistics(subgraph_table: dict):
    motif_table: dict = {}
    for key in subgraph_table.keys():
        new_key = ""
        new_key += key.get_label()
        # new_key += components.html(key.draw_graph())
        motif_table[new_key] = subgraph_table[key]
    df = pd.DataFrame.from_dict(motif_table, orient="index")
    st.table(df)


# returns a dictionary of all stastical information for each unique subgraph in graphs
def process_statistics(original_graph: GraphWithSubgraph, graphs: list[GraphWithSubgraph]) -> dict:
    subgraph_table: dict = {}  # subgraph -> [frequency, mean, sd, zscore, p-value]
    _generate_empty_subgraph_table(original_graph, subgraph_table)
    total_number_of_subgraphs = sum(original_graph.subgraph_list_enumerated.values())
    print(f"process_statistics: total_number_of_subgraphs = {total_number_of_subgraphs}")
    for subgraph in subgraph_table:
        original_freq = (
            original_graph.subgraph_list_enumerated[subgraph] / total_number_of_subgraphs
        )
        mean = _getMean(subgraph, graphs)
        if mean == 0:
            sd = "NA"
            z_score = "NA"
            p_value = "NA"
        else:
            sd = _getStandardDeviation(mean, subgraph, graphs)
            if sd == 0:
                z_score = "NA"
                p_value = "NA"
            else:
                z_score = _getZScore(sd, mean, subgraph, original_graph)
                p_value = _getPValue(z_score)
        # frequency of subgraph in original graph as a percent
        subgraph_table[subgraph]["freq"] = original_freq * 100
        subgraph_table[subgraph]["mean"] = mean * 100  # % mean-frequency as a percent
        subgraph_table[subgraph]["sd"] = sd  # standard deviation
        subgraph_table[subgraph]["z-score"] = z_score  # z-score
        subgraph_table[subgraph]["p-value"] = p_value  # p-value
    return subgraph_table


def _generate_empty_subgraph_table(graph: GraphWithSubgraph, subgraph_table: dict):
    # Create an empty set to store unique keys
    unique_keys = set()

    # Add the keys of the current dictionary to the set
    unique_keys.update(graph.subgraph_list_enumerated.keys())

    for key in unique_keys:
        subgraph_table[key] = {"freq": 0, "mean": 0, "sd": 0, "z-score": 0, "p-value": 0}


def _getMean(subgraph: Subgraph, graphs: list[GraphWithSubgraph]):
    frequencys = 0
    for graph in graphs:
        if subgraph in graph.subgraph_list_enumerated:
            graph_frequency = graph.subgraph_list_enumerated[subgraph]
            total_number_of_subgraphs = sum(graph.subgraph_list_enumerated.values())
            frequencys += graph_frequency / total_number_of_subgraphs
            # st.write(graph_frequency)
            # st.write(total_number_of_subgraphs)
            # st.write(frequencys)
    return frequencys / len(graphs)


def _getStandardDeviation(mean, subgraph: Subgraph, graphs: list[GraphWithSubgraph]):
    variance = 0
    for graph in graphs:
        if subgraph in graph.subgraph_list_enumerated:
            xi = graph.subgraph_list_enumerated[subgraph] / graph.total_subgraphs
            variance += (xi - mean) ** 2
        else:
            variance += 0
    variance = variance / (len(graphs) - 1)
    return variance**0.5


def _getZScore(sd: float, mean: float, subgraph: Subgraph, original_graph: GraphWithSubgraph):
    score = 0
    if subgraph in original_graph.subgraph_list_enumerated:
        # score as a frequency ratio
        score = original_graph.subgraph_list_enumerated[subgraph] / original_graph.total_subgraphs
    return (score - mean) / sd


def _getPValue(zscore: float):
    return scipy.stats.norm.sf(abs(zscore)) * 2
