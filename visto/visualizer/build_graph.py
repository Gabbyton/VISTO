import re
from collections import defaultdict
from os import path
from uuid import uuid4

import matplotlib.pyplot as plt
import networkx as nx
from bs4 import BeautifulSoup as bs
from cemento.draw_io.read_area_diagram import ReadAreaDiagram
from networkx.exception import NodeNotFound

from visto.connector.ontology import Ontology
from visto.connector.ref_ontology import RefOntology
from visto.visualizer.visualizer_ref import VisualizerRef

# TODO: convert to detecting primary relationships from a config file and treating all others as secondary or ontology-related
SECONDARY_RELS = ["mds:place"]


def visualize_graph(graph):
    # visualize the network for debugging
    plt.figure(figsize=(8, 8))
    pos = nx.planar_layout(graph)
    labels = nx.get_node_attributes(graph, "content")
    nx.draw(
        graph,
        pos,
        labels=labels,
        with_labels=True,
        node_color="skyblue",
        node_size=100,
        edge_color="grey",
        font_size=8,
        font_color="black",
    )
    plt.show()


# function to extract ontology information from ontology nodes
def get_term_mapping(term, symbol="[]"):
    term_mapping = re.match(rf"(.*)\{symbol[0]}(.*)\{symbol[1]}", term)
    if term_mapping:
        result = tuple(
            bs(text, "html.parser").get_text().strip() for text in term_mapping.groups()
        )
        term_class, content = result[0], result[1].split("|")
        if len(content) > 1:
            return term_class, content[0], content[1]
        return term_class, content[0]
    return None


# helper function to remove html tags in node content
def clean_term(term):
    term = bs(term, "html.parser").get_text().strip()
    term_mapping = re.match(r"(.*)\[(.*)\]", term)
    if term_mapping:
        return term_mapping.group(1)
    return term


def build_graph(file_path, save_triples=True):
    # read the area diagram and retrieve relationships
    fs_ex = ReadAreaDiagram(file_path)
    df = fs_ex.get_relationships()

    # create a priority table for edges
    edge_weight = defaultdict(int)
    edge_weight["mds:place"] = 1
    edge_weight["mds:bind"] = 2
    edge_weight["mds:define"] = 3
    edge_weight["mds:link"] = 4
    edge_weight["mds:adopt"] = 5
    # create graph representation of user diagram using relationships
    ex_graph = nx.DiGraph()
    for _, row in df.iterrows():
        ex_graph.add_node(row["parent_id"], content=row["parent"])
        ex_graph.add_node(row["child_id"], content=row["child"])
        ex_graph.add_edge(
            row["parent_id"],
            row["child_id"],
            rel=row["rel"],
            rel_id=row["rel_id"],
            weight=edge_weight[row["rel"]],
        )

    # retrieve the area nodes from the graph and assign to graph
    # retrieve the area to area connections only
    visited = set(ex_graph.nodes())
    uuid_header = str(uuid4()).split("-")[-1]
    new_rel_ct = 1

    for key, values in fs_ex.get_node_designations(parse_values=True).items():
        key_id, key_value = key
        # if term is isolated (does not have any relationships), add the term
        if key_id not in visited:
            ex_graph.add_node(key_id, content=key_value)
            visited.add(key_id)
        for value_id, value in values:
            if "~" in value:
                if value_id not in visited:
                    ex_graph.add_node(value_id, content=value)
                    visited.add(value_id)

                new_rel_id = f"{uuid_header}-{new_rel_ct}"
                new_rel_type = "mds:bind"
                new_rel_ct += 1

                ex_graph.add_edge(
                    key_id,
                    value_id,
                    rel=new_rel_type,
                    rel_id=new_rel_id,
                    area_connection=True,
                    weight=edge_weight[new_rel_type],
                )

    # separate primary from secondary node traversal to prevent non-tree structures
    secondary_rels = [
        (parent, child, data)
        for parent, child, data in ex_graph.edges(data=True)
        if data["rel"] in SECONDARY_RELS
    ]
    # remove the secondary rels from the original graph
    ex_graph.remove_edges_from(secondary_rels)
    # keep, but take note the nodes that will be isolated from the disconnection
    isolates = [
        node
        for node in nx.isolates(ex_graph)
        if "~" not in ex_graph.nodes[node]["content"]
    ]

    # create subgraphs to parse new area connections
    subgraphs = [
        ex_graph.subgraph(c).copy() for c in nx.weakly_connected_components(ex_graph)
    ]

    # retrieve the area to node connection only
    # create a temp graph that only includes area connections
    area_conn_graph = nx.DiGraph()
    area_conn_graph.add_edges_from(
        [edge for edge in ex_graph.edges(data=True) if "area_connection" in edge[2]]
    )

    # create a filtered dictionary from area designations that only includes root nodes
    component_roots = set(next(nx.topological_sort(subgraph)) for subgraph in subgraphs)
    # do not consider isolates as component roots
    component_roots -= set(isolates)
    root_area_designations = {
        node_id: area_ids
        for node_id, area_ids in fs_ex.get_area_designations().items()
        if node_id in component_roots
    }

    # assign component status to root nodes
    # exclude area nodes to avoid shallow renames
    non_area_component_roots = component_roots - set(area_conn_graph.nodes())
    is_component = {
        node: (node in non_area_component_roots) for node in ex_graph.nodes()
    }
    nx.set_node_attributes(ex_graph, is_component, "is_component")

    # traverse over root nodes to only connect encapsulating innermost areas
    for node_id, area_ids in root_area_designations.items():
        for area_id in area_ids:
            # given current subtrees, area nodes directly connected to nodes do not have children
            if len(nx.descendants(area_conn_graph, area_id)) == 0:
                new_rel_id = f"{uuid_header}-{new_rel_ct}"
                new_rel_type = "mds:bind"
                new_rel_ct += 1

                ex_graph.add_edge(
                    area_id,
                    node_id,
                    rel=new_rel_type,
                    rel_id=new_rel_id,
                    weight=edge_weight[new_rel_type],
                )

    # compute subgraphs again, to reflect new bindings
    subgraphs = [
        ex_graph.subgraph(c).copy() for c in nx.weakly_connected_components(ex_graph)
    ]

    motor_ref = RefOntology("motor_ref")
    link_onto = RefOntology("db_identifier")
    ontologies = dict()
    root_ontologies = dict()

    # create terms whenever applicable
    # TODO: change node retrieval to a more global analog
    for node_id, data in ex_graph.nodes(data=True):
        node_label = data["content"]
        is_component = data["is_component"]
        term_mapping = get_term_mapping(node_label)
        if term_mapping and node_id not in ontologies:
            name, base_ontology, self_term = term_mapping
            ontologies[node_id] = Ontology(
                name, self_term, base_ontology, is_component=is_component
            )

    # only remove isolates once their respective ontologies have been created, if any
    ex_graph.remove_nodes_from(isolates)
    # compute subgraphs again, to reflect isolate removal
    subgraphs = [
        ex_graph.subgraph(c).copy() for c in nx.weakly_connected_components(ex_graph)
    ]

    # traverse each resultant subtree and perform operations
    for subgraph in subgraphs:
        # retrieve root (component) node
        root = next(nx.topological_sort(subgraph))

        # define and sort traversal based on edge weights
        # only go through primary (tree-based relationships) first
        reverse_traversal = reversed(list(nx.edge_bfs(subgraph, root)))
        prioritized_traversal = sorted(
            reverse_traversal,
            key=lambda edge: subgraph.get_edge_data(edge[0], edge[1])["weight"],
            reverse=True,
        )

        # traverse through graphs and parse node relationships
        for parent_id, child_id in prioritized_traversal:
            # parent = subgraph.nodes[parent_id]["content"]
            child = subgraph.nodes[child_id]["content"]
            rel = subgraph.get_edge_data(parent_id, child_id)["rel"]

            if rel == "mds:bind":
                parent_onto = ontologies[parent_id]
                child_onto = ontologies[child_id]
                try:
                    parent_onto.bind(child_onto)
                except NodeNotFound:
                    # TODO: save node info to list for error output later
                    # TODO: create custom errors for this script
                    pass

            if rel == "mds:adopt":
                parent_onto = ontologies[parent_id]
                model = clean_term(child)
                parent_onto.adopt(motor_ref, model)

            if rel == "mds:define":
                parent_onto = ontologies[parent_id]
                value, variable = get_term_mapping(child, symbol="()")
                parent_onto.define(variable, value)

            if rel == "mds:link":
                parent_onto = ontologies[parent_id]
                try:
                    uid, variable = get_term_mapping(child, symbol="()")
                except TypeError:
                    uid = child
                    variable = None
                parent_onto.link(link_onto, uid, variable=variable)

        root_ontology = ontologies[root]

        # go over secondary (non-localized) traversals next
        for parent_id, child_id, data in secondary_rels:
            parent_onto = ontologies[parent_id]
            child_onto = ontologies[child_id]

            # if the child ended up being an isolate, first, add its respective ontology graph to the root graph
            if child_onto.get_name() not in root_ontology.get_graph().nodes():
                root_ontology.set_graph(
                    nx.compose(root_ontology.get_graph(), child_onto.get_graph())
                )

            if data["rel"] == "mds:place":
                new_rel_id = f"{uuid_header}-{new_rel_ct}"
                new_rel_ct += 1

                # proceed to connect the ontologies
                root_ontology.get_graph().add_edge(
                    parent_onto.get_name(),
                    child_onto.get_name(),
                    rel=data["rel"],
                    rel_id=new_rel_id,
                    is_rank=False,
                )

        if save_triples:
            # save each resultant subtree in a separate file
            output_path = VisualizerRef().get_triple_output_path()
            save_file_name = root_ontology.get_name().replace("~", "").strip()
            save_file_path = path.join(output_path, f"{save_file_name}.xlsx")
            root_ontology.get_rels().to_excel(save_file_path)

        root_ontologies[root] = root_ontology

    return root_ontologies
