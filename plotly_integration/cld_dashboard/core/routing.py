# core/routing.py
"""
Enhanced routing system for CLD Dashboard with SEC integration
"""

from dash import html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs, urlparse


def create_page_router(app):
    """
    Create page routing callback for the dashboard

    Args:
        app: Dash app instance
    """

    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
        Input("url", "search"),
        prevent_initial_call=False
    )
    def route_pages(pathname, search):
        """
        Route to different pages based on URL pathname and query parameters

        Args:
            pathname (str): URL pathname
            search (str): URL query string

        Returns:
            Dash component for the requested page
        """
        # Parse query parameters
        query_params = parse_qs(search.lstrip('?')) if search else {}

        try:
            # Dashboard Home
            if pathname == "/" or pathname == "/dashboard":
                from ..core.dashboard_home import create_dashboard_home_layout
                return create_dashboard_home_layout()

            # FB Samples Management
            elif pathname == "/fb-samples/view":
                from ..samples.layouts.sample_sets import create_all_samples_layout
                return create_all_samples_layout()

            elif pathname == "/fb-samples/sets":
                from ..samples.layouts.sample_sets import create_sample_sets_layout
                return create_sample_sets_layout()

            elif pathname == "/fb-samples/create":
                from ..samples.layouts.sample_sets import create_create_samples_layout
                return create_create_samples_layout()

            # SEC Analytics
            elif pathname == "/sec/dashboard":
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_dashboard_layout
                return create_sec_dashboard_layout()

            elif pathname == "/sec/sample-sets":
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_sample_sets_layout
                return create_sec_sample_sets_layout()

            elif pathname == "/sec/reports":
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_reports_layout
                return create_sec_reports_layout()

            elif pathname == "/sec/request":
                # Handle SEC analysis request
                sample_ids = query_params.get('samples', [''])[0].split(',') if 'samples' in query_params else []
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_request_layout
                return create_sec_request_layout(sample_ids)

            elif pathname == "/sec/analyze":
                # Embedded SEC analysis page
                sample_ids = query_params.get('samples', [''])[0].split(',') if 'samples' in query_params else []
                from ..embedded_apps.sec_integration.sec_embedder import create_sec_analysis_page
                return create_sec_analysis_page(sample_ids)

            # Settings
            elif pathname == "/settings":
                return create_settings_layout()

            # 404 Not Found
            else:
                return create_404_layout(pathname)

        except Exception as e:
            # Error handling
            return create_error_layout(str(e), pathname)


def create_404_layout(pathname):
    """Create 404 not found page"""
    return html.Div([
        dbc.Alert([
            html.H4("404 - Page Not Found", className="alert-heading"),
            html.P(f"The page '{pathname}' doesn't exist."),
            html.Hr(),
            html.P([
                "Go back to ",
                dbc.Button("Dashboard", href="/", color="primary", outline=True, size="sm"),
                " or try one of these pages:"
            ]),
            dbc.ButtonGroup([
                dbc.Button("FB Samples", href="/fb-samples/view", color="outline-secondary", size="sm"),
                dbc.Button("Sample Sets", href="/fb-samples/sets", color="outline-secondary", size="sm"),
                dbc.Button("SEC Analytics", href="/sec/dashboard", color="outline-secondary", size="sm"),
            ])
        ], color="warning")
    ], style={"padding": "50px"})


def create_error_layout(error_message, pathname=None):
    """Create error page layout"""
    return html.Div([
        dbc.Alert([
            html.H4([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Application Error"
            ], className="alert-heading"),
            html.P(f"An error occurred while loading the page: {error_message}"),
            html.Hr(),
            html.P([
                "Please try refreshing the page or go back to the ",
                dbc.Button("Dashboard", href="/", color="danger", outline=True, size="sm")
            ]),
            html.Details([
                html.Summary("Error Details"),
                html.Pre(error_message, className="mt-2 p-2 bg-light border rounded")
            ]) if error_message else None
        ], color="danger")
    ], style={"padding": "50px"})


def create_settings_layout():
    """Create settings page layout"""
    return html.Div([
        html.H3("⚙️ Settings", className="text-primary mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Dashboard Configuration", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("Dashboard settings and configuration options will be available here."),
                        html.Hr(),
                        dbc.Button("Reset to Defaults", color="outline-warning", size="sm"),
                    ])
                ])
            ], md=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("SEC Integration Settings", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("Configure SEC analysis integration settings."),
                        html.Hr(),
                        dbc.Button("Test SEC Connection", color="outline-info", size="sm"),
                    ])
                ])
            ], md=6)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Application Info", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Dl([
                            html.Dt("Version"),
                            html.Dd("3.0.0-beta"),
                            html.Dt("Last Updated"),
                            html.Dd("January 2025"),
                            html.Dt("Features"),
                            html.Dd("Enhanced SEC Integration, Sample Set Management")
                        ])
                    ])
                ])
            ], md=12)
        ])

    ], style={"padding": "20px"})


def create_breadcrumb_navigation(app):
    """
    Create breadcrumb navigation callback

    Args:
        app: Dash app instance
    """

    @app.callback(
        Output("breadcrumb-nav", "children"),
        Input("url", "pathname"),
        prevent_initial_call=True
    )
    def update_breadcrumbs(pathname):
        """Update breadcrumb navigation based on current page"""

        breadcrumbs = [
            dbc.BreadcrumbItem("Dashboard", href="/", active=(pathname == "/"))
        ]

        if pathname.startswith("/fb-samples"):
            breadcrumbs.append(
                dbc.BreadcrumbItem("FB Samples", href="/fb-samples/view",
                                   active=(pathname == "/fb-samples/view"))
            )

            if "/sets" in pathname:
                breadcrumbs.append(
                    dbc.BreadcrumbItem("Sample Sets", active=True)
                )
            elif "/create" in pathname:
                breadcrumbs.append(
                    dbc.BreadcrumbItem("Create Samples", active=True)
                )

        elif pathname.startswith("/sec"):
            breadcrumbs.append(
                dbc.BreadcrumbItem("SEC Analytics", href="/sec/dashboard",
                                   active=(pathname == "/sec/dashboard"))
            )

            if "/sample-sets" in pathname:
                breadcrumbs.append(
                    dbc.BreadcrumbItem("SEC Sample Sets", active=True)
                )
            elif "/reports" in pathname:
                breadcrumbs.append(
                    dbc.BreadcrumbItem("SEC Reports", active=True)
                )
            elif "/analyze" in pathname:
                breadcrumbs.append(
                    dbc.BreadcrumbItem("SEC Analysis", active=True)
                )

        elif pathname == "/settings":
            breadcrumbs.append(
                dbc.BreadcrumbItem("Settings", active=True)
            )

        return dbc.Breadcrumb(breadcrumbs)


def create_sidebar_navigation():
    """Create sidebar navigation component"""
    from ..shared.styles.common_styles import SIDEBAR_STYLE, ICONS

    return html.Div([
        html.H4("🧬 CLD Analytics", className="text-primary mb-3"),
        html.Hr(),

        dbc.Nav([
            # Dashboard
            dbc.NavLink([
                html.I(className=f"fas {ICONS['dashboard']} me-2"),
                "Dashboard"
            ], href="/", active="exact"),

            html.Hr(className="my-2"),

            # Sample Management
            html.P("SAMPLE MANAGEMENT", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className=f"fas {ICONS['samples']} me-2"),
                "View All Samples"
            ], href="/fb-samples/view", active="exact"),
            dbc.NavLink([
                html.I(className=f"fas {ICONS['sample_sets']} me-2"),
                "Sample Sets"
            ], href="/fb-samples/sets", active="exact"),
            dbc.NavLink([
                html.I(className=f"fas {ICONS['add']} me-2"),
                "Add Samples"
            ], href="/fb-samples/create", active="exact"),

            html.Hr(className="my-2"),

            # SEC Analytics
            html.P("SEC ANALYTICS", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className=f"fas {ICONS['analytics']} me-2"),
                "SEC Overview"
            ], href="/sec/dashboard", active="exact"),
            dbc.NavLink([
                html.I(className=f"fas {ICONS['sec']} me-2"),
                "SEC Sample Sets"
            ], href="/sec/sample-sets", active="exact"),
            dbc.NavLink([
                html.I(className=f"fas {ICONS['reports']} me-2"),
                "SEC Reports"
            ], href="/sec/reports", active="exact"),

            html.Hr(className="my-2"),

            # System
            html.P("SYSTEM", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className=f"fas {ICONS['settings']} me-2"),
                "Settings"
            ], href="/settings", active="exact")

        ], vertical=True, pills=True)
    ], style=SIDEBAR_STYLE)


def create_main_layout():
    """Create the main application layout with routing"""
    from ..shared.styles.common_styles import CONTENT_STYLE

    return html.Div([
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="app-state", data={}),

        # Sidebar navigation
        create_sidebar_navigation(),

        # Main content area
        html.Div([
            # Breadcrumb navigation
            html.Div(id="breadcrumb-nav", className="mb-3"),

            # Page content
            html.Div(id="page-content")

        ], style=CONTENT_STYLE)
    ])