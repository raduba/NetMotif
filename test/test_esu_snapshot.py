from lib import compute_label_frequencies, DATA_DIR
from src.graph_types import GraphType


def eg_test_helper(size: int, snapshot, graph_type: GraphType):
    frequencies = compute_label_frequencies(str(DATA_DIR / "exampleGraph.txt"), size, graph_type)
    assert frequencies == snapshot


def test_eg_size1u(snapshot):
    eg_test_helper(1, snapshot, GraphType.UNDIRECTED)


def test_eg_size1d(snapshot):
    eg_test_helper(1, snapshot, GraphType.DIRECTED)


def test_eg_size2u(snapshot):
    eg_test_helper(2, snapshot, GraphType.UNDIRECTED)


def test_eg_size2d(snapshot):
    eg_test_helper(2, snapshot, GraphType.DIRECTED)


def test_eg_size3u(snapshot):
    eg_test_helper(3, snapshot, GraphType.UNDIRECTED)


def test_eg_size3d(snapshot):
    eg_test_helper(3, snapshot, GraphType.DIRECTED)


def test_eg_size4u(snapshot):
    eg_test_helper(4, snapshot, GraphType.UNDIRECTED)


def test_eg_size4d(snapshot):
    eg_test_helper(4, snapshot, GraphType.DIRECTED)


def test_eg_size5u(snapshot):
    eg_test_helper(5, snapshot, GraphType.UNDIRECTED)


def test_eg_size5d(snapshot):
    eg_test_helper(5, snapshot, GraphType.DIRECTED)
