import streamlit as st
import time
import os
import io
from src.graph_with_subgraph import GraphWithSubgraph, NemoOutputType
from src.graph_types import GraphType
import src.random_graph as rg
import src.motif_statistics as stat
from src.paths import PROJECT_ROOT

st.set_page_config(page_title="NEMO motif detection program")
st.title("NEMO motif detection program")


def form_callback(start_time):
    """
    Handle form validation logic
    """

    if st.session_state.get("uploaded_file") is None:
        st.warning("Please upload a file.")
        return

    if st.session_state.get("graph_type") is None:
        st.warning("Please select a graph type.")
        return

    nemo_output_type = NemoOutputType.NEMO_COUNT
    if st.session_state["nemo_count_option"] == "SubgraphProfile":
        nemo_output_type = NemoOutputType.SUBGRAPH_PROFILE
    elif st.session_state["nemo_count_option"] == "SubgraphCollection":
        nemo_output_type = NemoOutputType.SUBGRAPH_COLLECTION

    k = st.session_state["motif_size"]

    probabilities = None
    if st.session_state.get("is_sampling_selected", False):
        probabilities = st.session_state.get("input_probabilities", None)
        if probabilities is None or len(probabilities) != k:
            st.warning("Please select sampling probabilities at each level.")
            return

    # create graph from file
    G = GraphWithSubgraph(
        graph_type=st.session_state["graph_type"],
        input=st.session_state["uploaded_file"],
        motif_size=k,
        nemo_type=nemo_output_type,
        probabilities=probabilities,
    )

    # display graph properties
    graph_properties = G.get_graph_properties()
    st.write(f"Number of nodes: {graph_properties['Number of nodes']}")
    st.write(f"Number of edges: {graph_properties['Number of edges']}")
    st.write(f"Weight: {graph_properties['Weight']}")
    st.write(f"Number of subgraphs: {graph_properties['Number of subgraphs']}")

    # visualize the full graph if selected
    if st.session_state["is_visualize_graph"]:
        st.markdown("### Full Graph Visualization")
        G.draw_graph()

    # Visualize subgraphs if selected
    if st.session_state["is_visualize_subgraph"]:
        st.markdown("### Subgraph Visualization")
        G.draw_subgraph()

    if (
        st.session_state.get("number_of_random_graphs") is not None
        and st.session_state["number_of_random_graphs"] > 0
    ):
        # Generate random graphs
        random_graphs = rg.generate_random_graphs(
            G,
            st.session_state["number_of_random_graphs"],
            G.motif_size,
            probabilities=probabilities,
        )

        stats = stat.process_statistics(G, random_graphs)
        end_time = time.time()

        # Visualize statistics
        st.markdown("### Statistics Table")
        stat.draw_statistics(stats)
    else:
        end_time = time.time()

    elapsed_time = end_time - start_time
    st.write(f"Time elapsed: {elapsed_time:.2f} seconds")

    # Download button if nemo count option is selected to subgraph collection
    G.generate_download_button()


def main():
    # Initialize global session state for user form submission
    if "graph_type" not in st.session_state:
        st.session_state["graph_type"] = None
    if "uploaded_file" not in st.session_state:
        st.session_state["uploaded_file"] = None
    if "prev_uploaded_file" not in st.session_state:
        st.session_state["prev_uploaded_file"] = None

    uploaded_file = st.file_uploader("Graph File", label_visibility="hidden")
    if uploaded_file:
        if uploaded_file != st.session_state["prev_uploaded_file"]:
            st.session_state["uploaded_file"] = uploaded_file
            st.session_state["prev_uploaded_file"] = uploaded_file
            st.toast("Successfully uploaded file", icon="✅")

    demo = st.button("Use Demo File")
    if demo:
        demo_path = os.path.join(PROJECT_ROOT, "data", "bestTest.txt")
        if os.path.exists(demo_path):
            with open(demo_path, "rb") as file:
                file_content = file.read()

            # Simulate an uploaded file using BytesIO
            uploaded_file = io.BytesIO(file_content)
            uploaded_file.name = "bestTest.txt"
            uploaded_file.type = "text/plain"

            st.session_state["uploaded_file"] = uploaded_file
            st.session_state["prev_uploaded_file"] = uploaded_file
            st.toast("Successfully uploaded demo file", icon="✅")

    col1, col2 = st.columns([1, 2])
    with col1:
        graph_type = st.radio(
            "Set Graph type:",
            key="graph",
            options=[GraphType.UNDIRECTED, GraphType.DIRECTED],
            format_func=lambda x: x.value,
        )

        motif_size = st.number_input(
            "Size of motif",
            value=3,
            placeholder="Input motif size...",
            min_value=1,
            max_value=8,
        )

        number_of_random_graphs = st.number_input(
            "Number of random graphs",
            value=20,
            placeholder="Input number of graphs...",
            min_value=0,
            max_value=1000,
        )

        nemo_count_type = st.radio(
            "Nemo Data Options",
            key="nemo_option",
            options=["NemoCount", "SubgraphProfile", "SubgraphCollection"],
        )

        use_sampling = st.checkbox("Use Sampling")
        input_probabilities = []
        if use_sampling:
            for i in range(motif_size):
                p = st.number_input(
                    f"Probability on level {i + 1}",
                    key=f"prob_{i}",
                    value=0.5,
                    min_value=0.0,
                    max_value=1.0,
                )
                input_probabilities.append(p)

    with col2:
        st.write("NOTE: Uploading more than 1000 nodes might consume more processing time.")
        st.write("Visualize Options:")
        is_visualize_graph = st.checkbox("Visualize graph")
        is_visualize_subgraph = st.checkbox("Visualize subgraph")

    submitted = st.button(label="Submit")

    if submitted:
        st.session_state["is_visualize_graph"] = is_visualize_graph
        st.session_state["is_visualize_subgraph"] = is_visualize_subgraph

        st.session_state["graph_type"] = graph_type
        st.session_state["motif_size"] = motif_size
        st.session_state["number_of_random_graphs"] = number_of_random_graphs
        st.session_state["nemo_count_option"] = nemo_count_type

        st.session_state["is_sampling_selected"] = use_sampling
        if use_sampling:
            st.session_state["input_probabilities"] = input_probabilities
        else:
            st.session_state["input_probabilities"] = None

        start_time = time.time()
        form_callback(start_time)

    st.markdown("<br>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
