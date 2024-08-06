from dash import html, dcc
import dash_bootstrap_components as dbc

no_node_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Cannot Select Node")),
                dbc.ModalBody("Node not in the variable graph."),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ms-auto", n_clicks=0)
                ),
            ],
            id="no-node-modal",
            is_open=False,
        ),
    ]
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem(
                    dcc.Upload("Import File...", id="file-upload"), href="#"
                ),
            ],
            nav=True,
            in_navbar=True,
            label="File",
        ),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem(
                    dcc.Upload(
                        "Adjust Panels...",
                        id="view-adjust-panels",
                        multiple=False,
                        accept=".drawio",
                    ),
                    href="#",
                ),
            ],
            nav=True,
            in_navbar=True,
            label="View",
        ),
        dbc.NavItem(dbc.NavLink("About", href="#")),
        dbc.NavItem(dbc.NavLink("Help", href="#")),
    ],
    brand="VISTO",
    brand_href="#",
    color="light",
    dark=False,
    links_left=True,
)