import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html

from visto.visualizer.serializers import read_json_graph

input_pane = html.Div(
    [
        dbc.Label("x-axis variable"),
        dbc.Select(
            id="x-axis-select",
            options=[],
        ),
        dbc.Label("y-axis variable"),
        dbc.Select(id="y-axis-select", options=[]),
    ]
)

plotter_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Variable Plotter")),
        dbc.ModalBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div("Select variables for the x and y axis:"),
                                html.Br(),
                                input_pane,
                                html.Br(),
                                dbc.Button("Plot", id="plot-button"),
                            ]
                        ),
                        dbc.Col(
                            [
                                dcc.Graph(id="variable-plot", figure={}),
                            ],
                            width=8,
                        ),
                    ]
                ),
            ]
        ),
    ],
    id="plotter-modal",
    size="xl",
    is_open=False,
    keyboard=False,
    backdrop="static",
)


@callback(
    Output("x-axis-select", "options"),
    Output("y-axis-select", "options"),
    Input("for-plotting-nodes-store", "data"),
    State("experiment-graph-store", "data"),
    prevent_initial_call=True,
)
def update_plotter_options(nodes_for_plotting, experiment_graph):
    experiment_graph = read_json_graph(experiment_graph)

    # TODO: add discovery method for finding timestamp resource
    options = [{"label": "timestamp", "value": 0}]
    for label in nodes_for_plotting:
        value = experiment_graph.nodes[label]["resource"]
        options.append({"label": label, "value": value})
    return options, options


@callback(
    Output("plot-button", "disabled"),
    Input("x-axis-select", "value"),
    Input("y-axis-select", "value"),
)
def toggle_plot_buton(x_axis_value, y_axis_value):
    return not (x_axis_value and y_axis_value)


@callback(
    Output("variable-plot", "figure"),
    Input("plot-button", "n_clicks"),
    State("x-axis-select", "value"),
    State("y-axis-select", "value"),
    State("source-file-store", "data"),
    prevent_initial_call=True,
)
def plot(n_clicks, x_axis_value, y_axis_value, source_file_path):
    x_axis_value = int(x_axis_value)
    y_axis_value = int(y_axis_value)
    df = pd.read_csv(source_file_path, usecols=[x_axis_value, y_axis_value])
    df_cols = df.columns.tolist()
    fig = px.line(df, x=df_cols[0], y=df_cols[-1])
    return fig
