import json
import networkx as nx
def read_json_graph(graph):
    return nx.node_link_graph(json.loads(graph))