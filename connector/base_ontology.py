import networkx as nx
import pandas as pd
from bidict import bidict
from cemento.draw_io.read_diagram import ReadDiagram
from cemento.tree import Tree

from connector.data_ref import DataRef


class BaseOntology:

    def __init__(self, name, self_term=None, base_ontology=None, ref=None):
        self._name = name
        self._base_ontology = base_ontology
        self._ref = ref
        self._self_term = self_term
        self._term_ref = bidict()
        self._graph = None
        self._parent = None
        self.graph_vars = None

        if ref is None:
            self._ref = DataRef()

        if base_ontology is not None:
            self.set_base_ontology(base_ontology)

        # populate term reference with initial values
        for graph_var in self.get_graph_vars():
            self._term_ref[graph_var] = graph_var

    def _define_graph(self):
        base_ontology_path = self.get_ref().get_ontology_path(self.get_base_ontology())
        ontology = ReadDiagram(base_ontology_path, inverted_rank_arrows=False)

        rels_df = ontology.get_relationships()

        # generate graph from edge table
        graph = nx.DiGraph()
        for _, row in rels_df.iterrows():
            parent, child, rel, is_rank = (
                row["parent"],
                row["child"],
                row["rel"],
                row["is_rank"],
            )
            graph.add_edge(parent, child, rel=rel, is_rank=is_rank)

        # determine rank type for each node
        node_is_rank = {node: (":" in node) for node in graph.nodes()}
        nx.set_node_attributes(graph, node_is_rank, "is_rank")

        # determine node type from root
        term_type = dict()
        ranked_edges = [edge for edge in graph.edges(data=True) if edge[2]["is_rank"]]
        ranked_graph = nx.DiGraph(ranked_edges)
        tree = Tree(graph=ranked_graph)
        for _, subtree in enumerate(tree.get_subgraphs()):
            subgraph = subtree.get_graph()
            root = next(nx.topological_sort(subgraph))
            for node in subgraph.nodes():
                term_type[node] = root
        nx.set_node_attributes(graph, term_type, "type")

        self.set_graph(graph)

    def _replace_node(self, node, replacement, ignore_ref=False):
        if node == replacement:
            return

        nx.relabel_nodes(self.get_graph(), {node: replacement}, copy=False)

        if not ignore_ref:
            self.set_term(node, replacement)

    def get_name(self):
        return self._name

    def get_base_ontology(self):
        return self._base_ontology

    def get_graph(self):
        return self._graph

    def set_graph(self, graph):
        self._graph = graph

    def get_parent(self):
        return self._parent

    def set_parent(self, parent):
        if self.get_parent() is not None:
            raise ValueError(
                "Cannot assign parent twice. Please create a new object or refrain from setting again."
            )
        self._parent = parent

    def get_ref(self):
        return self._ref

    def get_self_term(self):
        return self._self_term

    def get_graph_vars(self):
        return {node for node in self.get_nodes() if node.endswith("_")}

    def get_term_ref(self):
        return self._term_ref

    def set_term(self, key, value):
        self._term_ref[key] = value

    def get_term(self, key):
        return self._term_ref[key]

    def get_term_key(self, value):
        return self._term_ref.inverse[value]

    def get_nodes(self, include_rank=True):
        if not include_rank:
            return [node for node in self.get_graph().nodes() if ":" not in node]
        return self.get_graph().nodes()

    def set_base_ontology(self, base_ontology):
        self._define_graph()

    def get_rels(self):
        entries = []
        for edge in self.get_graph().edges(data=True):
            parent, child, data = edge
            entries.append(
                {
                    "parent": parent,
                    "child": child,
                    "rel": data["rel"],
                    "is_rank": data["is_rank"],
                }
            )
        return pd.DataFrame(entries)
