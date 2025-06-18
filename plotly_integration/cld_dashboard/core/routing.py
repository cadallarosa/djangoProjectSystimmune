# Enhanced routing system for CLD Dashboard - Streamlined without breadcrumbs

from dash import html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs
from ..shared.styles.common_styles import SIDEBAR_STYLE, ICONS
from ..config.app_urls import get_navigation_links, INTERNAL_ROUTES


def create_sidebar_navigation():
    """Create sidebar navigation component with hash links"""
    nav_links = get_navigation_links()

    sidebar_content = []

    # Dashboard header
    sidebar_content.extend([
        html.Div([
            html.H4("CLD Dashboard", className="text-primary mb-3"),
            html.Hr()
        ])
    ])

    # Main navigation - Updated for hash routing
    for section_name, links in nav_links.items():
        if section_name != "main":
            sidebar_content.append(
                html.P(section_name.replace("_", " ").upper(),
                       className="text-muted small fw-bold mb-1 mt-3")
            )

        nav_items = []
        for link in links:
            # Convert to hash-based URLs
            hash_url = f"#!/{link['url'].lstrip('/')}" if link['url'] != "/" else "#!/"
            nav_items.append(
                html.A([
                    html.I(className=f"fas {link['icon']} me-2"),
                    link['name']
                ],
                    href=hash_url,
                    className="nav-link",
                    style={
                        "color": "#212529",
                        "textDecoration": "none",
                        "padding": "0.5rem 0.75rem",
                        "borderRadius": "0.375rem",
                        "display": "block",
                        "marginBottom": "0.25rem"
                    })
            )

        sidebar_content.append(
            html.Div(nav_items, className="mb-2")
        )

        if section_name == "main":
            sidebar_content.append(html.Hr())

    return html.Div(sidebar_content, style=SIDEBAR_STYLE)


def create_page_router(app):
    """
    Create page routing callbacks for hash-based routing - No breadcrumbs

    Args:
        app: Dash app instance
    """

    @app.callback(
        Output("sidebar-nav", "children"),
        Input("parsed-pathname", "data"),
        prevent_initial_call=False
    )
    def render_sidebar(pathname):
        """Render sidebar navigation"""
        return create_sidebar_navigation()

    # REMOVED breadcrumb callback - no longer needed

    @app.callback(
        Output("page-content", "children"),
        Input("parsed-pathname", "data"),
        Input("url", "search"),
        prevent_initial_call=False
    )
    def route_pages(pathname, search):
        """
        Route to different pages based on URL pathname (now from hash)

        Args:
            pathname (str): URL pathname (extracted from hash)
            search (str): URL query string

        Returns:
            Dash component for the requested page
        """
        # Parse query parameters
        query_params = parse_qs(search.lstrip('?')) if search else {}

        # Debug print to see what pathname we're getting
        print(f"Routing to pathname: '{pathname}'")

        # Home/Dashboard
        if pathname == "/" or pathname == "/dashboard" or pathname == "" or pathname is None:
            from ..core.dashboard_home import create_dashboard_layout
            return create_dashboard_layout()

        # Sample Sets
        elif pathname == "/sample-sets":
            try:
                from ..samples.layouts.sample_sets import create_sample_sets_overview_layout
                return create_sample_sets_overview_layout()
            except ImportError:
                return html.Div([
                    html.H2("Sample Sets"),
                    html.P("Sample sets page - placeholder")
                ])

        elif pathname == "/sample-sets/table":
            try:
                from ..samples.layouts.sample_sets import create_sample_sets_table_layout
                return create_sample_sets_table_layout()
            except ImportError:
                return html.Div([
                    html.H2("Sample Sets - Table View"),
                    html.P("Sample sets table page - placeholder")
                ])

        elif pathname == "/sample-sets/view":
            try:
                from ..samples.layouts.sample_sets import create_sample_set_detail_layout
                return create_sample_set_detail_layout(query_params)
            except ImportError:
                return html.Div([
                    html.H2("Sample Set Details"),
                    html.P("Sample set detail page - placeholder")
                ])

        # Individual Samples
        elif pathname == "/samples/view":
            try:
                from ..samples.layouts.view_samples import create_view_samples_layout
                return create_view_samples_layout()
            except ImportError:
                return html.Div([
                    html.H2("View Samples"),
                    html.P("View samples page - placeholder")
                ])

        elif pathname == "/samples/create":
            try:
                from ..samples.layouts.create_samples import create_create_samples_layout
                return create_create_samples_layout()
            except ImportError:
                return html.Div([
                    html.H2("Create Samples"),
                    html.P("Create samples page - placeholder")
                ])

        # SEC Analysis
        elif pathname == "/analysis/sec":
            try:
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_dashboard_layout
                return create_sec_dashboard_layout()
            except ImportError:
                return html.Div([
                    html.H2("SEC Analysis"),
                    html.P("SEC analysis page - placeholder")
                ])

        elif pathname == "/analysis/sec/sample-sets":
            try:
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_sample_sets_layout
                return create_sec_sample_sets_layout()
            except ImportError:
                return html.Div([
                    html.H2("SEC Sample Sets"),
                    html.P("SEC sample sets page - placeholder")
                ])

        elif pathname == "/analysis/sec/reports":
            try:
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_reports_layout
                return create_sec_reports_layout()
            except ImportError:
                return html.Div([
                    html.H2("SEC Reports"),
                    html.P("SEC reports page - placeholder")
                ])

        elif pathname == "/analysis/sec/report":
            try:
                from ..embedded_apps.sec_integration.sec_embedder import create_embedded_sec_report
                return create_embedded_sec_report(query_params)
            except ImportError:
                return html.Div([
                    html.H2("SEC Report"),
                    html.P("SEC embedded report page - placeholder")
                ])

        # Settings
        elif pathname == "/settings":
            from ..core.dashboard_home import create_settings_layout
            return create_settings_layout()

        # Help
        elif pathname == "/help":
            return create_help_layout()

        # Default case
        else:
            from ..core.dashboard_home import create_dashboard_layout
            return create_dashboard_layout()


def create_help_layout():
    """Create help page layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Help & Documentation"),
                html.Hr(),

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Getting Started", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P(
                            "Welcome to the CLD Dashboard v3. This application uses hash-based routing for better URL handling."),
                        html.Ul([
                            html.Li("All URLs use hash routing (#!/path/to/page)"),
                            html.Li("URLs are now shareable and reloadable"),
                            html.Li("Use the sidebar to navigate between sections"),
                            html.Li("Bookmark any page - they all work!")
                        ])
                    ])
                ], className="mb-4"),

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Hash-Based URLs", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("This dashboard uses hash-based routing for better URL persistence:"),
                        html.Ul([
                            html.Li("#!/samples/view - View all samples"),
                            html.Li("#!/samples/create - Create new samples"),
                            html.Li("#!/sample-sets/table - Sample sets table"),
                            html.Li("#!/analysis/sec - SEC analysis dashboard")
                        ]),
                        html.P("These URLs can be bookmarked, shared, and reloaded safely!", className="text-success")
                    ])
                ])
            ])
        ])
    ], style={"padding": "20px"})