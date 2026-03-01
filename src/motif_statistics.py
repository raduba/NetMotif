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
        subgraph_stats = subgraph_table[key]
        motif_table[new_key] = {
            statkey: _num_fmt(subgraph_stats[statkey]) for statkey in subgraph_stats
        }
    df = pd.DataFrame.from_dict(motif_table, orient="index")
    st.table(df)


def _num_fmt(val: float | None) -> str:
    if val is None:
        return "NA"
    return f"{val:.4f}"


# returns a dictionary of all stastical information for each unique subgraph in graphs
def process_statistics(
    original_graph: GraphWithSubgraph, graphs: list[GraphWithSubgraph]
) -> dict[Subgraph, dict[str, float | None]]:
    subgraph_table: dict = {}  # subgraph -> [frequency, mean, sd, zscore, p-value]
    _generate_empty_subgraph_table(original_graph, subgraph_table)
    total_number_of_subgraphs = sum(original_graph.subgraph_list_enumerated.values())
    print(f"process_statistics: total_number_of_subgraphs = {total_number_of_subgraphs}")
    for subgraph in subgraph_table:
        print(
            f"label count for {subgraph.get_label()}: "
            f"{original_graph.subgraph_list_enumerated[subgraph]}"
        )
        original_freq = (
            original_graph.subgraph_list_enumerated[subgraph] / total_number_of_subgraphs
        )
        mean = _getMean(subgraph, graphs)
        if mean == 0:
            sd = None
            z_score = None
            p_value = None
        else:
            sd = _getStandardDeviation(mean, subgraph, graphs)
            if sd == 0:
                z_score = None
                p_value = None
            else:
                z_score = _getZScore(sd, mean, subgraph, original_graph)
                p_value = _getPValue(z_score)

        # Frequency and mean are percentages
        if original_freq is not None:
            original_freq *= 100
        if mean is not None:
            mean *= 100

        subgraph_table[subgraph]["freq"] = original_freq
        subgraph_table[subgraph]["mean"] = mean
        subgraph_table[subgraph]["sd"] = sd
        subgraph_table[subgraph]["z-score"] = z_score
        subgraph_table[subgraph]["p-value"] = p_value
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


def _getStandardDeviation(mean, subgraph: Subgraph, graphs: list[GraphWithSubgraph]) -> float:
    variance = 0
    for graph in graphs:
        if subgraph in graph.subgraph_list_enumerated:
            xi = graph.subgraph_list_enumerated[subgraph] / graph.total_subgraphs
            variance += (xi - mean) ** 2
        else:
            variance += 0
    variance = variance / (len(graphs) - 1)
    return variance**0.5


def _getZScore(
    sd: float, mean: float, subgraph: Subgraph, original_graph: GraphWithSubgraph
) -> float:
    score = 0.0
    if subgraph in original_graph.subgraph_list_enumerated:
        # score as a frequency ratio
        score = original_graph.subgraph_list_enumerated[subgraph] / original_graph.total_subgraphs
    return (score - mean) / sd


def _getPValue(zscore: float) -> float:
    return scipy.stats.norm.sf(abs(zscore)) * 2.0
