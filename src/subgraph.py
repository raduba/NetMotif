from src.graph_utils import Graph


class Subgraph(Graph):
    """
    A graph of same size as motif. GraphWithSubgraphs --<*> Subgraphs
    """

    def __init__(self, graph_type, input, node_ids):
        super().__init__(graph_type, input)  # Call the parent's __init__
        # Original vertex IDs in the parent graph
        self.node_ids = node_ids

    def __eq__(self, other):
        if isinstance(other, Subgraph):
            return self.label == other.label
        else:
            return False

    def __hash__(self):
        return hash(self.label)

    def get_label(self):
        return self.label

    def set_label(self, input_label):
        self.label = input_label
