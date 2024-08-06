import networkx as nx

from connector.base_ontology import BaseOntology


class Ontology(BaseOntology):

    def __init__(self, name, self_term, base_ontology, ref=None, is_component=False):
        self._is_component = is_component
        self._child_connector = None
        self._children = set()
        super().__init__(
            name, self_term=self_term, base_ontology=base_ontology, ref=ref
        )

        self._define_self_term()
        self._self_term_map()

    def define(self, key, value, ignore_ref=False):
        # TODO: replace blanket replacement guard with guard against parent renaming
        # if key not in self.get_graph_vars():
        #     raise KeyError(f"They key {key} does not exist or is already set.")

        self._replace_node(key, value, ignore_ref=ignore_ref)

    def _define_self_term(self):
        curr_self_term = self.get_term(self.get_self_term())

        if curr_self_term is None:
            curr_self_term = self.get_self_term()

        self._replace_node(curr_self_term, self.get_name())

    def graph_map(self, substitutions, ignore_ref=False):
        for key, value in substitutions.items():
            self._replace_node(key, value, ignore_ref=ignore_ref)

    def _self_term_map(self):
        substitutions = dict()
        graph = self.get_graph()
        self_name = self.get_name()
        for node in nx.descendants(graph, self_name):
            if node.endswith("_") and "*" not in node:
                substitutions[node] = f"{self_name} {node[:-1]}"
        self.graph_map(substitutions)

    def _parent_map(self):
        if self.get_parent() is None:
            return

        parent_name = self.get_parent().get_name()
        substitutions = dict()
        for var in self.get_graph_vars():
            substitutions[var] = f"{parent_name} {var[:-1]}"

        self.graph_map(substitutions)

    def link(self, link_ontology, uid, variable=None):
        if variable is None:
            characteristics = {
                child
                for parent, child, data in self.get_graph().edges(data=True)
                if data["rel"] == "pmd:characteristic"
            }
            if len(characteristics) != 1:
                message = "Cannot infer variable to link. The number of characteristic variables in this ontology is not one."
                if len(characteristics) > 1:
                    message += (
                        f"Other characteristics include: {', '.join(characteristics)}"
                    )
                raise AttributeError(message)

            variable = self.get_term_key(next(iter(characteristics)))

        if variable not in self.get_term_ref().keys():
            raise AttributeError(
                f"The provided variable {variable} is not in the graph."
            )

        variable = self.get_term(variable)
        self.set_graph(nx.compose(self.get_graph(), link_ontology.get_graph().copy()))
        # TODO: replace with less fixed solution, i.e. get rid of the string hardcodes
        db_identifier = "db_identifier_"
        self.get_graph().add_edge(
            variable, db_identifier, rel="pmd:resource", is_rank=False
        )
        self._replace_node(db_identifier, str(uid), ignore_ref=True)

    def bind(self, child_onto):
        # set parent of child
        child_onto.set_parent(self)
        # add child
        self.add_child(child_onto)
        # get relevant graphs
        parent_graph = self.get_graph()
        child_graph = child_onto.get_graph()
        # find the connecting path to the child
        parent_term = self.get_self_term()
        child_term = child_onto.get_term(child_onto.get_self_term())
        # keep the path nodes
        path = nx.shortest_path(child_graph, parent_term, child_term)
        keep_nodes = set([child_onto.get_term_key(node) for node in path])
        # set the second to the last term (i.e. ancestor of child term) as the connector
        self.set_child_connector(path[-2])
        # rename connecting terms to parent's version
        substitutions = dict()
        for node_key in keep_nodes:
            if node_key in self.get_term_ref().keys():
                curr_node = child_onto.get_term(node_key)
                # replace only if the value has not been substituted
                if curr_node == node_key:
                    substitutions[node_key] = self.get_term(node_key)
        child_onto.graph_map(substitutions)

        # only map if the component is a root component node
        if self.is_component():
            child_onto._parent_map()

        self.set_graph(nx.compose(parent_graph, child_graph))

    # TODO: impermanent solution. Please replace with modular ontology-driven OOP later
    def adopt(self, ref, model):
        ref_graph = ref.get_graph().copy()
        # save the model node and its descendants
        keep_nodes = {model}
        keep_nodes |= set(nx.descendants(ref_graph, model))
        # save the rank predecessors of each included node
        # first create a graph with just ancestor connections
        rank_edges = [
            (u, v, d) for (u, v, d) in ref_graph.edges(data=True) if d["is_rank"]
        ]
        rank_graph = nx.DiGraph(rank_edges)
        # then simply add the ancestors of the nodes already added in a set
        extra_nodes = set()
        for node in keep_nodes:
            extra_nodes |= set(nx.ancestors(rank_graph, node))
        keep_nodes |= extra_nodes
        # remove nodes that are not marked to keep
        ref_graph.remove_nodes_from(
            [node for node in ref_graph.nodes() if node not in keep_nodes]
        )
        # relabel node model to current node name and combine graphs
        nx.relabel_nodes(ref_graph, {model: self.get_name()}, copy=False)
        self.set_graph(nx.compose(self.get_graph(), ref_graph))
        # remove the template placeholder variables from the original graph

        self.get_graph().remove_nodes_from(
            [node for node in self.get_nodes() if "*" in node]
        )
        # rename the added variables using the newly connected current term
        self._self_term_map()

    def add_child(self, child_onto):
        self._children.add(child_onto)

    def get_children(self):
        return self._children

    def get_child_connector(self):
        return self._child_connector

    def set_child_connector(self, connector_term):
        self._child_connector = connector_term

    def is_component(self):
        return self._is_component
