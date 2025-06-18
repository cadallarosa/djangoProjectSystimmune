import dash_bootstrap_components as dbc
from dash import html


def create_embedded_iframe(src_url, title="Embedded Application", height="800px", show_controls=True):
    """
    Create an embedded iframe component for external Dash apps

    Args:
        src_url (str): URL of the app to embed
        title (str): Title for the iframe
        height (str): Height of the iframe
        show_controls (bool): Whether to show header controls

    Returns:
        dbc.Card: Card containing the embedded iframe
    """
    header_content = [html.H5(title, className="mb-0")]

    if show_controls:
        header_content.append(
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-external-link-alt me-1"),
                    "Open in New Tab"
                ],
                    href=src_url,
                    target="_blank",
                    color="outline-primary",
                    size="sm"),
                dbc.Button([
                    html.I(className="fas fa-sync-alt me-1"),
                    "Refresh"
                ],
                    id={"type": "iframe-refresh", "index": title},
                    color="outline-secondary",
                    size="sm")
            ], className="float-end")
        )

    return dbc.Card([
        dbc.CardHeader(header_content) if show_controls else None,
        dbc.CardBody([
            html.Iframe(
                id={"type": "embedded-iframe", "index": title},
                src=src_url,
                style={
                    "width": "100%",
                    "height": height,
                    "border": "none",
                    "border-radius": "5px" if not show_controls else "0 0 5px 5px"
                }
            )
        ], style={"padding": "0"})
    ], className="shadow")


def create_loading_iframe(title="Loading Application...", height="800px"):
    """
    Create a loading placeholder for iframe content

    Args:
        title (str): Loading message
        height (str): Height of the loading area

    Returns:
        dbc.Card: Card with loading spinner
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                dbc.Spinner(
                    html.Div(id="loading-content"),
                    size="lg",
                    color="primary",
                    type="border"
                ),
                html.H5(title, className="mt-3 text-muted")
            ],
                style={
                    "height": height,
                    "display": "flex",
                    "flex-direction": "column",
                    "justify-content": "center",
                    "align-items": "center",
                    "text-align": "center"
                })
        ])
    ], className="shadow")


def create_error_iframe(error_message="Application failed to load", height="800px"):
    """
    Create an error display for failed iframe loading

    Args:
        error_message (str): Error message to display
        height (str): Height of the error area

    Returns:
        dbc.Card: Card with error message
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-exclamation-triangle fa-3x text-danger mb-3"),
                html.H5("Application Error", className="text-danger"),
                html.P(error_message, className="text-muted"),
                dbc.Button([
                    html.I(className="fas fa-redo me-1"),
                    "Retry"
                ],
                    color="outline-primary",
                    id="retry-iframe-btn")
            ],
                style={
                    "height": height,
                    "display": "flex",
                    "flex-direction": "column",
                    "justify-content": "center",
                    "align-items": "center",
                    "text-align": "center"
                })
        ])
    ], className="shadow")