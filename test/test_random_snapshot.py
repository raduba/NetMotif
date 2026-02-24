from src.graph_types import GraphType
from src.graph_utils import Graph
from src.random_graph import generate_random_graphs
from lib import DATA_DIR, get_label_frequencies

SEED = 12345678
sample_graph = Graph(GraphType.UNDIRECTED, str(DATA_DIR / "exampleGraph.txt"))


def random_test_helper(size: int, snapshot):
    random_graph = generate_random_graphs(sample_graph, 1, size, seed=SEED)[0]
    frequencies = get_label_frequencies(random_graph)
    assert frequencies == snapshot


def test_random_size1(snapshot):
    random_test_helper(1, snapshot)


def test_random_size2(snapshot):
    random_test_helper(2, snapshot)


def test_random_size3(snapshot):
    random_test_helper(3, snapshot)


def test_random_size4(snapshot):
    random_test_helper(4, snapshot)


def test_random_size5(snapshot):
    random_test_helper(5, snapshot)
