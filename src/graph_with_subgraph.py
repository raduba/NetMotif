import gzip
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from io import TextIOWrapper
from typing import Dict, Any
import networkx as nx
import os
import streamlit as st
from src.graph_utils import Graph
from src.subgraph import Subgraph
from src.esu import ESU


class NemoOutputType(Enum):
    NEMO_COUNT = 1
    SUBGRAPH_PROFILE = 2
    SUBGRAPH_COLLECTION = 3


@dataclass
class DownloadInfo:
    download_filename: str
    download_label: str


_DOWNLOAD_FILE_INFO = {
    NemoOutputType.SUBGRAPH_PROFILE: DownloadInfo(
        download_filename="subgraph_profile.txt.gz", download_label="Download subgraph profile"
    ),
    NemoOutputType.SUBGRAPH_COLLECTION: DownloadInfo(
        download_filename="subgraph_collection.txt.gz",
        download_label="Download subgraph collection",
    ),
}


class GraphWithSubgraph(Graph):
    def __init__(
        self, graph_type, input, motif_size, esu=None, nemo_type=NemoOutputType.NEMO_COUNT
    ):
        # instantiation of Graph object
        super().__init__(graph_type, input)
        self._nemo_type: NemoOutputType = nemo_type
        self._download_file_path: str | None = None
        self._download_file: TextIOWrapper | tempfile._TemporaryFileWrapper[str] | None = None
        # label -> dict[Node, int] ; label to node counter
        self._nodes_dictionary: dict[str, dict[Any, int]] = defaultdict(lambda: defaultdict(int))
        self._esu_callback = None
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
            try:
                self._init_download_file()
                self.esu = ESU(self.G, motif_size, graph_type, self._esu_callback)
            finally:
                if self._download_file:
                    self._format_download_file()
                    self._download_file.close()
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

    def __del__(self):
        """Delete the temporary file when this object goes out of scope."""
        if self._download_file_path and os.path.exists(self._download_file_path):
            try:
                print(f"deleting temporary file: {self._download_file_path}")
                os.remove(self._download_file_path)
            except Exception as e:
                print(f"Failed to remove {self._download_file_path}: {e}")

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

    def _init_download_file(self):
        """
        Create a temporary file and keep it open so that the ESU callbacks can directly write the
        subgraph info to the file. The file is deleted by the class destructor.
        """
        file_info = _DOWNLOAD_FILE_INFO.get(self._nemo_type, None)
        if file_info is None:
            return

        temp_file = tempfile.NamedTemporaryFile(
            mode="w", prefix="nemo_", delete=False, suffix=".txt.gz"
        )

        self._download_file_path = temp_file.name
        temp_file.close()

        self._download_file = gzip.open(self._download_file_path, "wt")
        print(f"temp download file created: {self._download_file_path}")

        if self._nemo_type == NemoOutputType.SUBGRAPH_COLLECTION:
            self._esu_callback = self._write_subgraph_collections
        elif self._nemo_type == NemoOutputType.SUBGRAPH_PROFILE:
            self._esu_callback = self._update_subgraph_profile

    def _write_subgraph_collections(self, canonical_label: str, data: list):
        """
        ESU callback function for handling subgraph collection data.
        Append the canonical label and the data subgraph to the download file.
        """
        nodes = ", ".join((str(x) for x in data))
        self._download_file.write(f"{canonical_label}[{nodes}]\n")

    def _update_subgraph_profile(self, canonical_label: str, data: list):
        """
        ESU callback function for handling subgraph profile data.
        Update the node count for each canonical label.
        Data will be saved in the download file after ESU completes by the _format_download_file
          method.
        """
        for node in data:
            self._nodes_dictionary[canonical_label][node] += 1

    def _format_download_file(self):
        """
        Perform the final writing to the download file after ESU completes.
        Currently, only SUBGRAPH_PROFILE needs to write the profile matrix to the download file.
        SUBGRAPH_COLLECTION updates the file on every ESU callback and does not need to perform
        special formatting on completion.
        """
        if self._nemo_type == NemoOutputType.SUBGRAPH_PROFILE:
            top_row = f"{'Nodes':<10}"  # top row for graph labels
            for key in self._nodes_dictionary:
                top_row += f"{key.strip():<10}"  # strip new line from label
            top_row += "\n"  # make space for the nodes and their count
            self._download_file.write(top_row)
            # each nodes count in its associated graph
            for node in self.G:
                line = f"{node:<10}"
                for key in self._nodes_dictionary:
                    line += f"{self._nodes_dictionary[key][node]:<10}"
                line += "\n"
                self._download_file.writelines(line)

    def generate_download_button(self):
        file_info = _DOWNLOAD_FILE_INFO.get(self._nemo_type, None)
        if file_info is None or self._download_file_path is None:
            return None

        if os.path.exists(self._download_file_path):
            with open(self._download_file_path, "rb") as download_file:
                return st.download_button(
                    label=file_info.download_label,
                    data=download_file,
                    file_name=file_info.download_filename,
                )

        return None
