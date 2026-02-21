from test.lib import compute_label_frequencies, DATA_DIR

def eg_test_helper(size: int, snapshot):
    frequencies = compute_label_frequencies(str(DATA_DIR / "exampleGraph.txt"), size=size)
    assert frequencies == snapshot

def test_eg_size1(snapshot):
    eg_test_helper(1, snapshot)

def test_eg_size2(snapshot):
    eg_test_helper(2, snapshot)

def test_eg_size3(snapshot):
    eg_test_helper(3, snapshot)

def test_eg_size4(snapshot):
    eg_test_helper(4, snapshot)
