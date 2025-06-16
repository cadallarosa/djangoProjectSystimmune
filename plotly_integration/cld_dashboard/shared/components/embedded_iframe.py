# shared/components/embedded_iframe.py
"""
Embedded iframe component for integrating external Dash apps
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from urllib.parse import urlencode


def create_embedded_iframe(src_url, height="800px", title="Embedded App", **kwargs):
    """
    Create an embedded iframe component

    Args:
        src_url (str): URL of the app to embed
        height (str): Height of the iframe
        title (str): Title for the iframe
        **kwargs: Additional iframe attributes

    Returns:
        dash component with iframe
    """
    default_style = {
        'width': '100%',
        'height': height,
        'border': '1px solid #ddd',
        'border-radius': '8px'
    }

    # Merge any custom styles
    iframe_style = {**default_style, **kwargs.get('style', {})}

    return html.Div([
        html.Iframe(
            src=src_url,
            style=iframe_style,
            title=title,
            **{k: v for k, v in kwargs.items() if k != 'style'}
        )
    ])


def create_sec_report_iframe(sample_ids=None, report_id=None, hide_report_tab=True):
    """
    Create an iframe specifically for SEC Report App

    Args:
        sample_ids (list): List of sample IDs to pre-load
        report_id (int): Specific report ID to load
        hide_report_tab (bool): Whether to hide the report selection tab

    Returns:
        Embedded iframe for SEC analysis
    """
    base_url = "/plotly_integration/dash-app/app/SecReportApp2/"
    params = {}

    if report_id:
        params['report_id'] = report_id

    if hide_report_tab:
        params['hide_report_tab'] = 'true'

    # If sample_ids provided, we'll use sample view mode
    if sample_ids:
        # This will trigger the SecReportApp2 to create a temporary report
        params['samples'] = ','.join(sample_ids)
        params['mode'] = 'samples'

    # Build URL with parameters
    if params:
        url = f"{base_url}?{urlencode(params)}"
    else:
        url = base_url

    return create_embedded_iframe(
        src_url=url,
        height="900px",
        title="SEC Analysis Report"
    )


def create_loading_iframe_placeholder():
    """Create a loading placeholder for iframe content"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Spinner([
                html.Div([
                    html.H4("Loading SEC Analysis...", className="text-center mb-3"),
                    html.P("Please wait while the analysis application loads.",
                           className="text-center text-muted")
                ])
            ], size="lg", color="primary")
        ], className="text-center p-5")
    ], style={'height': '400px', 'display': 'flex', 'align-items': 'center'})


def create_iframe_with_loading(src_url, loading_timeout=3000, **kwargs):
    """
    Create iframe with loading state

    Args:
        src_url (str): URL to embed
        loading_timeout (int): Timeout for loading state in ms
        **kwargs: Additional iframe parameters
    """
    return html.Div([
        # Loading placeholder
        html.Div(
            create_loading_iframe_placeholder(),
            id="iframe-loading-placeholder",
            style={'display': 'block'}
        ),

        # Actual iframe (hidden initially)
        html.Div(
            create_embedded_iframe(src_url, **kwargs),
            id="iframe-content",
            style={'display': 'none'}
        ),

        # JavaScript to handle loading
        dcc.Interval(
            id="iframe-loading-interval",
            interval=loading_timeout,
            n_intervals=0,
            max_intervals=1
        )
    ])


def create_error_iframe_placeholder(error_message="Failed to load application"):
    """Create an error placeholder for failed iframe loads"""
    return dbc.Alert([
        html.H4([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Application Load Error"
        ], className="alert-heading"),
        html.P(error_message),
        html.Hr(),
        dbc.Button(
            "Retry Loading",
            id="retry-iframe-btn",
            color="warning",
            outline=True
        )
    ], color="warning")


def create_sec_analysis_embed_layout(sample_set_data):
    """
    Create complete layout for embedded SEC analysis

    Args:
        sample_set_data (dict): Data about the sample set including:
            - sample_ids: List of sample IDs
            - project: Project name
            - sip_number: SIP number
            - development_stage: Development stage

    Returns:
        Complete layout with header and embedded SEC app
    """
    sample_ids = sample_set_data.get('sample_ids', [])
    project = sample_set_data.get('project', 'Unknown')
    sip = sample_set_data.get('sip_number', 'Unknown')
    dev_stage = sample_set_data.get('development_stage', 'Unknown')

    return html.Div([
        # Header section
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H4([
                            html.I(className="fas fa-microscope me-2"),
                            "SEC Analysis"
                        ], className="text-primary mb-1"),
                        html.P([
                            html.Strong("Project: "), project, " | ",
                            html.Strong("SIP: "), sip, " | ",
                            html.Strong("Stage: "), dev_stage
                        ], className="text-muted mb-2"),
                        html.P([
                            html.Strong("Samples: "),
                            ", ".join(sample_ids[:5]),
                            f" (+{len(sample_ids) - 5} more)" if len(sample_ids) > 5 else ""
                        ], className="small text-info")
                    ], md=8),
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-arrow-left me-2"),
                            "Back to Sample Sets"
                        ],
                            href="/sec/sample-sets",
                            color="outline-secondary",
                            size="sm")
                    ], md=4, className="text-end")
                ])
            ])
        ], className="mb-3"),

        # Embedded SEC app
        create_sec_report_iframe(sample_ids=sample_ids, hide_report_tab=True)
    ])