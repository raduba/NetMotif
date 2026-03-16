from src.graph_types import GraphType
from src.graph_utils import Graph
from src.random_graph import generate_random_graphs
from lib import DATA_DIR, get_label_frequencies

SEED = 12345678
sample_graph_u = Graph(GraphType.UNDIRECTED, str(DATA_DIR / "exampleGraph.txt"))
sample_graph_d = Graph(GraphType.DIRECTED, str(DATA_DIR / "exampleGraph.txt"))


def random_test_helper(size: int, snapshot, graph_type: GraphType):
    random_graph = generate_random_graphs(
        sample_graph_u if graph_type == GraphType.UNDIRECTED else sample_graph_d, 1, size, seed=SEED
    )[0]
    frequencies = get_label_frequencies(random_graph)
    assert frequencies == snapshot


def test_random_size1u(snapshot):
    random_test_helper(1, snapshot, GraphType.UNDIRECTED)


def test_random_size1d(snapshot):
    random_test_helper(1, snapshot, GraphType.DIRECTED)


def test_random_size2u(snapshot):
    random_test_helper(2, snapshot, GraphType.UNDIRECTED)


def test_random_size2d(snapshot):
    random_test_helper(2, snapshot, GraphType.DIRECTED)


def test_random_size3u(snapshot):
    random_test_helper(3, snapshot, GraphType.UNDIRECTED)


def test_random_size3d(snapshot):
    random_test_helper(3, snapshot, GraphType.DIRECTED)


def test_random_size4u(snapshot):
    random_test_helper(4, snapshot, GraphType.UNDIRECTED)


def test_random_size4d(snapshot):
    random_test_helper(4, snapshot, GraphType.DIRECTED)


def test_random_size5u(snapshot):
    random_test_helper(5, snapshot, GraphType.UNDIRECTED)


def test_random_size5d(snapshot):
    random_test_helper(5, snapshot, GraphType.DIRECTED)
