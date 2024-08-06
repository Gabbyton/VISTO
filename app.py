import base64
import json
import math
from collections import defaultdict
from os import path, remove
from uuid import uuid4

import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import networkx as nx
from dash import Dash, Input, Output, State, callback, dcc, html, no_update

from visualizer.build_graph import build_graph
from visualizer.components import navbar, no_node_modal
from visualizer.plotter import plotter_modal
from visualizer.selector import selector
from visualizer.serializers import read_json_graph
from visualizer.stylesheet import default_stylesheet
from visualizer.visualizer_ref import VisualizerRef

NUM_PANELS = 6
NUM_COLS = 2
LAYOUT_FULLWIDTH = 12


def generate_panel_header(layout_idx):
    return dbc.Row(
        [
            dbc.Col(
                html.Div(
                    html.I("No Node Selected"),
                    id=f"cytoscape-caption-{layout_idx}",
                )
            ),
            dbc.Col(
                dbc.InputGroup(
                    [
                        dbc.Switch(
                            id=f"cytoscape-toggle-{layout_idx}",
                            value=False,
                            disabled=True,
                        ),
                        dbc.Label("Toggle types"),
                    ]
                )
            ),
        ],
        justify="end",
    )


def generate_cytoscape_layout(
    init_node_elements, num_panels=NUM_PANELS, num_cols=NUM_COLS
):
    cyto_layouts = []
    for layout_idx in range(6):
        cyto_layouts.append(
            cyto.Cytoscape(
                id=f"cytoscape-{layout_idx}",
                layout={"name": "cose"},
                style={"height": "400px"},
                elements=init_node_elements[layout_idx],
                stylesheet=default_stylesheet,
            )
        )

    num_rows = int(math.ceil(num_panels / num_cols))
    layout_rows = []
    for row_idx in range(num_rows):
        layout_cols = []
        for col_idx in range(num_cols):
            layout_idx = row_idx * num_cols + col_idx
            layout_cols.append(
                dbc.Col(
                    dbc.Col(
                        [
                            generate_panel_header(layout_idx),
                            cyto_layouts[layout_idx],
                        ],
                        style={"border": "solid"},
                        className="m-2",
                    ),
                    width=LAYOUT_FULLWIDTH // num_cols,
                )
            )
        layout_rows.append(dbc.Row(layout_cols))
    return layout_rows


cytoscape_layout = generate_cytoscape_layout(defaultdict(lambda: []))

visualizer_ref = VisualizerRef()
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(
    [
        dcc.Store(id="var-graph-store"),
        dcc.Store(id="experiment-graph-store"),
        dcc.Store(id="linked-nodes-store"),
        dcc.Store(id="selector-store", data=True),
        dcc.Store(id="for-plotting-nodes-store", data=[]),
        dcc.Store(id="for-adding-nodes-store", data=[]),
        dcc.Store(id="source-file-store", data=visualizer_ref.get_file_source_path()),
    ]
    + [navbar, no_node_modal, plotter_modal]
    + cytoscape_layout
    + [selector]
)


def generate_init_display_graph(file_path):
    # only get the first subtree for debugging
    experiment_graph = list(build_graph(file_path).values())[0].get_graph()
    # get all the linked nodes
    linked_nodes = {
        (parent, child)
        for parent, child, data in experiment_graph.edges(data=True)
        if data["rel"] == "pmd:resource"
    }
    # delete child nodes of this relationship for better viewing
    to_remove = {child for (parent, child) in linked_nodes}
    new_node_values = {parent: child for parent, child in linked_nodes}
    linked_nodes = {parent for (parent, child) in linked_nodes}

    experiment_graph.remove_nodes_from(to_remove)
    nx.set_node_attributes(experiment_graph, new_node_values, "resource")

    # only get the instance variables for display
    var_only_graph = experiment_graph.subgraph(
        [node for node in experiment_graph if ":" not in node or node.startswith("ex:")]
    )

    root = next(nx.topological_sort(var_only_graph))
    init_display_graph = nx.ego_graph(var_only_graph, root, radius=2)

    return experiment_graph, var_only_graph, init_display_graph, linked_nodes


def serialize_graph(graph, linked_nodes):
    graph_uuid = str(uuid4()).split("-")[-1]
    elements = []
    node_ids = dict()

    for node_ct, node in enumerate(graph.nodes()):
        node_id = f"{graph_uuid}-{node_ct}"
        node_ids[node] = node_id
        elements.append(
            {
                "data": {
                    "id": node_id,
                    "label": f"{node}",
                    "chosen": False,
                    "is_node": True,
                    "linked": node in linked_nodes,
                },
            }
        )

    for parent, child, data in graph.edges(data=True):
        parent_id, child_id = node_ids[parent], node_ids[child]
        elements.append(
            {
                "data": {
                    "source": parent_id,
                    "target": child_id,
                    "label": f"{data['rel']}",
                    "is_node": False,
                }
            }
        )

    return elements


@app.callback(
    Output("no-node-modal", "is_open", allow_duplicate=True),
    Input("close", "n_clicks"),
    State("no-node-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal(n, is_open):
    if n:
        return not is_open
    return is_open


for layout_idx in range(NUM_PANELS - 1):

    @callback(
        Output(f"cytoscape-{layout_idx+1}", "elements", allow_duplicate=True),
        Output(f"cytoscape-caption-{layout_idx+1}", "children"),
        Output("no-node-modal", "is_open", allow_duplicate=True),
        Input(f"cytoscape-{layout_idx}", "tapNode"),
        State("var-graph-store", "data"),
        State("experiment-graph-store", "data"),
        State("linked-nodes-store", "data"),
        State("selector-store", "data"),
        prevent_initial_call=True,
    )
    def select_ego_node(
        node_data, var_only_graph, experiment_graph, linked_nodes, selector_state
    ):
        if not selector_state:
            var_only_graph = read_json_graph(var_only_graph)
            experiment_graph = read_json_graph(experiment_graph)
            linked_nodes = json.loads(linked_nodes)

            if not node_data:
                return no_update

            if not node_data["data"]["label"]:
                return no_update

            if not var_only_graph or not experiment_graph:
                return no_update

            # generate a new graph from the node
            selected_node = node_data["data"]["label"]
            if selected_node not in var_only_graph.nodes():
                return no_update, no_update, True

            selected_var_graph = nx.ego_graph(var_only_graph, selected_node, radius=2)
            new_elements = serialize_graph(selected_var_graph, linked_nodes)

            for element in new_elements:
                element["data"]["chosen"] = element["data"]["label"] == selected_node

            return new_elements, selected_node, False

        return no_update


@callback(
    Output("cytoscape-0", "elements", allow_duplicate=True),
    Output("var-graph-store", "data"),
    Output("experiment-graph-store", "data"),
    Output("linked-nodes-store", "data"),
    Input("file-upload", "contents"),
    State("file-upload", "filename"),
    prevent_initial_call=True,
)
def upload_file(contents, filename):
    file_uuid = uuid4()
    if not contents or not filename:
        return no_update

    if not filename.endswith(".drawio"):
        return no_update

    temp_path = path.join(visualizer_ref.get_temp_path(), f"{file_uuid}-{filename}")
    with open(temp_path, "wb") as f:
        _, content = contents.split(",")
        decoded = base64.b64decode(content)
        f.write(decoded)

    try:
        experiment_graph, var_only_graph, init_display_graph, linked_nodes = (
            generate_init_display_graph(temp_path)
        )
    finally:
        remove(temp_path)

    new_elements = serialize_graph(init_display_graph, linked_nodes)
    return (
        new_elements,
        json.dumps(nx.node_link_data(var_only_graph)),
        json.dumps(nx.node_link_data(experiment_graph)),
        json.dumps(list(linked_nodes)),
    )


for layout_idx in range(NUM_PANELS):

    @callback(
        Output("for-adding-nodes-store", "data", allow_duplicate=True),
        Input(f"cytoscape-{layout_idx}", "selectedNodeData"),
        State("selector-store", "data"),
        prevent_initial_call=True,
    )
    def select_plot_node(selected_element_data, selector_state):
        if selector_state:
            selected_nodes = set()

            for element in selected_element_data:
                if element["is_node"] and element["linked"]:
                    selected_nodes.add(element["label"])

            return list(selected_nodes)

        return no_update

    @callback(
        Output(f"cytoscape-toggle-{layout_idx}", "disabled"),
        Input(f"cytoscape-{layout_idx}", "elements"),
    )
    def disable_toggle_button(data):
        if not data:
            return True
        return False

    @callback(
        Output(f"cytoscape-{layout_idx}", "elements", allow_duplicate=True),
        Input(f"cytoscape-toggle-{layout_idx}", "value"),
        State(f"cytoscape-{layout_idx}", "elements"),
        State("var-graph-store", "data"),
        State("experiment-graph-store", "data"),
        State("linked-nodes-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_type(
        toggle_true, elements, var_only_graph, experiment_graph, linked_nodes
    ):

        if (
            elements is None
            or var_only_graph is None
            or experiment_graph is None
            or linked_nodes is None
        ):
            return no_update

        var_only_graph = read_json_graph(var_only_graph)
        experiment_graph = read_json_graph(experiment_graph)
        linked_nodes = json.loads(linked_nodes)

        selected_node = None

        for element in elements:
            if element["data"]["is_node"] and element["data"]["chosen"]:
                selected_node = element["data"]["label"]
                break

        nodes = {
            element["data"]["label"]
            for element in elements
            if element["data"]["is_node"]
        }

        if toggle_true:
            new_nodes = set()
            for node in nodes:
                predecessors = {
                    predecessor
                    for predecessor in experiment_graph.predecessors(node)
                    if experiment_graph[predecessor][node]["is_rank"]
                }
                for predecessor in predecessors:
                    new_nodes |= {predecessor}
                    new_nodes |= nx.ancestors(experiment_graph, predecessor)

            nodes |= new_nodes
            new_elements = serialize_graph(
                experiment_graph.subgraph(nodes), linked_nodes
            )
        else:
            new_nodes = nodes & var_only_graph.nodes()
            new_elements = serialize_graph(
                var_only_graph.subgraph(new_nodes), linked_nodes
            )

        if selected_node:
            for element in new_elements:
                element["data"]["chosen"] = element["data"]["label"] == selected_node

        return new_elements


if __name__ == "__main__":
    app.run(debug=True)
