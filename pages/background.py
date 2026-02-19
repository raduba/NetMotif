import streamlit as st

st.set_page_config(page_title="Background and Algorithms")
st.title('Biological Background and Algorithms')

st.markdown(
"""
    ## Biological Background and Implications
    NEMO: network motif detection is a useful tool for identifying protein to protein 
    interactions in biological processes. Finding these gene expression patterns can aide in 
    identifying people who have genetic predispositions to diseases and find diseases
    earlier. In one example, researchers hypothesized that network motif detection can be
    useful to finding markers of metastasis, a malignant growth secondary to the primary 
    location of the cancer. Analyzing the gene expression through a network approach can 
    also find genetic alteration and find irregularities faster and more accurately than other methods. 
    Overall, with experimentation and improvements, network-based motif detection can improve current 
    disease detection methods and create change in the medical world. 
    ## Algorithms and Processes
    #### ESU: Enumerate Subgraphs
    The ESU algorithm accepts a graph as an input and finds all possible subgraphs of size K. 
    It returns all the subgraphs in a list to allow easy labeling of the subgraphs in the 
    next step. In this algorithm, there are 3 important lists to track: current node list which 
    tracks the current subgraph, neighbors list which tracks the next nodes to choose, and the 
    nodes visited set which keeps a set of all the nodes that have been visited at the current 
    recursion level. This process is completed recursively, with a few steps:\n
    1) For every node in the graph, it is added to the current node list and all its neighbors are 
    found.\n
    2) For every neighbor, the current neighbor is added to the current node list and its neighbors 
    are found and added to the next neighbor list.\n
    3) After the size n subgraph is found, the list is copied to a total subgraph list and the 
    function returns to the previous level to follow the same process for the next node. \n
    During this process, the visited node set is updated with each call to prevent repeated subgraphs. 
    Figure 4 contains a visual example of how this algorithm functions.

"""
)
st.image('./resources/ESUexample.png', caption='Figure 4')
st.markdown(
    """
    #### G6 Labeling
    g6, or graph6, labeling is a format that represents the connections between nodes. To start, 
    the first character of the label is always the size of the subgraph plus 63 converted to a character 
    using ASCII code. 63 is added because it represents the first ASCII character that can be used 
    for this format. Then, the connections of the graph are analyzed using an adjacency matrix where 
    1 represents a connection and 0 represents no connection between 
    nodes. Figure 5 shows an example of an adjacency matrix. Since the graph in g6 is undirected, 
    the matrix is mirrored along the diagonal, so 
    only the upper diagonal of the matrix is read. The matrix is read column by column, creating 
    a binary number. The binary number can then be added to 63 and converted to an ASCII character. 
    Combining the character found from size and the character(s) found from connection creates the 
    g6 label. g6 labeling has different outputs for isomorphic graphs, so the outputs need to be passed 
    into a canonical labeling software that converts the g6 label to a labeling system that has 
    a unique label for each non-isomorphic graph.
    """
)
st.image('./resources/adjacencyExample.png', caption='Figure 5')
st.markdown(
    """
    #### Random Graph Generation
    When testing if the input graph has any motifs, its subgraph frequencies need to be compared 
    against subgraph frequencies from random graphs of the same size and degree. To do this, an 
    n number of random graphs are generated. Each graph collects all the connections, as shown in 
    Figure 6, and puts them into a single list of all nodes, as shown in Figure 7. Finally, the nodes are  
    randomly matched together to make a new graph.
    """
)
st.image('./resources/figure6.png', caption='Figure 6')
st.image('./resources/figure7.png', caption='Figure 7')