import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update

SELECTOR_DISPLAY = {True: "Select Mode", False: "View Mode"}

selector = html.Div(
    dbc.Card(
        dbc.CardBody(
            [
                html.Span(
                    dbc.Button(
                        "View Mode",
                        color="light",
                        className="me-1",
                        size="lg",
                        id="select-state-button",
                    ),
                    className="right-border",
                ),
                html.Span(
                    dbc.Button(
                        [
                            "Add Selected",
                            dbc.Badge(
                                "0",
                                color="light",
                                text_color="secondary",
                                className="ms-1",
                                id="add-selected-button-badge",
                            ),
                        ],
                        id="add-selected-button",
                        color="secondary",
                        className="mx-2",
                        disabled=True,
                    )
                ),
                html.Span(
                    dbc.Button(
                        [
                            "Plotter",
                            dbc.Badge(
                                "0",
                                id="plotter-button-badge",
                                color="light",
                                text_color="primary",
                                className="ms-1",
                            ),
                        ],
                        id="plotter-button",
                        color="primary",
                    ),
                    className="ml-4",
                ),
            ]
        ),
        className="m-3",
    ),
    className="bottom-left",
)


@callback(
    Output("add-selected-button-badge", "children"),
    Input("for-adding-nodes-store", "data"),
)
def update_add_button_badge(nodes_to_add):
    return f"{len(nodes_to_add)}"


@callback(
    Output("plotter-button-badge", "children"),
    Input("for-plotting-nodes-store", "data"),
)
def update_plotter_button_badge(nodes_to_plot):
    return f"{len(nodes_to_plot)}"


@callback(
    Output("add-selected-button", "disabled"), Input("for-adding-nodes-store", "data")
)
def toggle_add_button(nodes_to_add):
    return len(nodes_to_add) <= 0


@callback(
    Output("plotter-button", "disabled"),
    Input("selector-store", "data"),
)
def toggle_plotter_button(selector_state):
    return not selector_state


@callback(
    Output("for-plotting-nodes-store", "data"),
    Output("for-adding-nodes-store", "data"),
    Input("add-selected-button", "n_clicks"),
    State("for-adding-nodes-store", "data"),
    State("for-plotting-nodes-store", "data"),
)
def add_selected_to_plot(n_clicks, nodes_to_add, nodes_to_plot):
    if not nodes_to_add:
        return no_update

    return list(set(nodes_to_plot + nodes_to_add)), []


@callback(
    Output("plotter-modal", "is_open"),
    Input("plotter-button", "n_clicks"),
    prevent_initial_call=True,
)
def open_plotter(n_clicks):
    return True


@callback(Output("select-state-button", "children"), Input("selector-store", "data"))
def update_selector_button(selector_state):
    if selector_state is None:
        return no_update

    return SELECTOR_DISPLAY[selector_state]


@callback(
    Output("selector-store", "data"),
    Input("select-state-button", "n_clicks"),
    State("selector-store", "data"),
)
def toggle_selector_state(n_clicks, selector_state):
    if selector_state is None:
        is_select = True

    is_select = not selector_state
    return is_select
