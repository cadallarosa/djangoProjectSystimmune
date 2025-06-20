# SEC embedder component with debugging - REPLACE your sec_embedder.py with this

from dash import html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs
from ...shared.components.embedded_iframe import create_embedded_iframe, create_loading_iframe, create_error_iframe
from plotly_integration.cld_dashboard.main_app import app


def create_embedded_sec_report(query_params):
    """
    Create embedded SEC report layout with debugging
    """
    print(f"🔍 SEC EMBEDDER - create_embedded_sec_report called")
    print(f"   Query params received: {query_params}")

    # Extract parameters
    report_id = query_params.get('report_id', [''])[0] if query_params else ''

    print(f"   Extracted report_id: {report_id}")

    return dbc.Container([
        # Debug info at top (remove in production)
        dbc.Alert([
            html.H6("Debug Info:"),
            html.P(f"Query Params: {query_params}"),
            html.P(f"Report ID: {report_id}")
        ], color="info", dismissable=True, id="debug-alert"),

        # Header
        dbc.Row([
            dbc.Col([
                html.H2("SEC Analysis Report"),
                html.P(f"Report ID: {report_id}" if report_id else "No report ID provided",
                       className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-1"),
                        "Back"
                    ], href="#!/sample-sets", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-external-link-alt me-1"),
                        "Open in New Tab"
                    ], id="open-sec-new-tab", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-sec-report", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Report info
        html.Div(id="sec-report-info", className="mb-3"),

        # Embedded SEC Application Container
        dbc.Row([
            dbc.Col([
                html.Div(id="sec-embed-container", children=[
                    create_loading_iframe("Loading SEC Application...", "900px")
                ])
            ])
        ])

    ], fluid=True, style={"padding": "20px"})



# @app.callback(
#     [Output("sec-embed-container", "children"),
#      Output("open-sec-new-tab", "href"),
#      Output("sec-report-info", "children")],
#     [Input("parsed-pathname", "data"),
#      Input("parsed-search", "data"),  # Use parsed-search instead
#      Input("refresh-sec-report", "n_clicks")],
#     prevent_initial_call=False
# )
# def load_sec_embed(pathname, search, refresh_clicks):
#     """Load the embedded SEC application"""
#     print(f"\n🔄 SEC EMBED CALLBACK")
#     print(f"   Pathname: {pathname}")
#     print(f"   Search: {search}")
#
#     # Check if we're on the right page
#     if not pathname or pathname != "/analysis/sec/report":
#         print(f"   ❌ Not on SEC report page")
#         return no_update, no_update, no_update
#
#     try:
#         # Parse query parameters
#         query_params = parse_qs(search.lstrip('?')) if search else {}
#         report_id = query_params.get('report_id', [''])[0]
#
#         print(f"   📊 Report ID: {report_id}")
#
#         if not report_id:
#             # No report ID
#             info_alert = dbc.Alert([
#                 html.I(className="fas fa-exclamation-triangle me-2"),
#                 "No report ID provided. Please select a sample set with an existing SEC report."
#             ], color="warning")
#
#             error_content = dbc.Card([
#                 dbc.CardBody([
#                     html.H5("No Report Selected"),
#                     html.P("Please go back to sample sets and select a report to view."),
#                     dbc.Button("Go to Sample Sets", href="#!/sample-sets", color="primary")
#                 ])
#             ], className="text-center")
#
#             return error_content, "#", info_alert
#
#         # Build SEC URL
#         sec_url = f"/plotly_integration/dash-app/app/SecReportApp2/?report_id={report_id}"
#
#         print(f"   ✅ SEC URL: {sec_url}")
#
#         # Create info
#         info_alert = dbc.Alert([
#             html.I(className="fas fa-file-alt me-2"),
#             html.Strong(f"SEC Report #{report_id}")
#         ], color="info")
#
#         # Create iframe
#         iframe_component = html.Div([
#             html.Iframe(
#                 src=sec_url,
#                 style={
#                     "width": "100%",
#                     "height": "900px",
#                     "border": "none",
#                     "borderRadius": "5px"
#                 }
#             )
#         ])
#
#         return iframe_component, sec_url, info_alert
#
#     except Exception as e:
#         print(f"   ❌ Error: {e}")
#         import traceback
#         traceback.print_exc()
#
#         error_alert = dbc.Alert([
#             html.H5("Error Loading Report"),
#             html.P(str(e))
#         ], color="danger")
#
#         return create_error_iframe(str(e)), "#", error_alert

@app.callback(
    [Output("sec-embed-container", "children"),
     Output("open-sec-new-tab", "href")],
    [Input("url", "href"),  # Use href instead of search
     Input("refresh-sec-report", "n_clicks")],
    [State("parsed-pathname", "data")]
)
def load_sec_embed(href, refresh_clicks, pathname):
    """Load the embedded SEC application with parameters"""
    print(f"🔄 SEC Embed Callback - pathname: {pathname}, href: {href}")

    if not pathname or not pathname.startswith("/analysis/sec/report"):
        return no_update, no_update

    try:
        # Extract query params from hash URL
        query_params = {}
        if href and '#!' in href and '?' in href:
            hash_part = href.split('#!')[1]
            if '?' in hash_part:
                search = '?' + hash_part.split('?')[1]
                query_params = parse_qs(search.lstrip('?'))

        report_id = query_params.get('report_id', [''])[0] if query_params.get('report_id') else ''

        print(f"📊 Building SEC URL - Report ID: {report_id}")

        # Build SEC report URL
        base_sec_url = "/plotly_integration/dash-app/app/SecReportApp2/"

        if report_id:
            sec_url = f"{base_sec_url}?report_id={report_id}"
        else:
            sec_url = base_sec_url

        print(f"✅ SEC URL: {sec_url}")

        # Create embedded iframe
        iframe_component = create_embedded_iframe(
            src_url=sec_url,
            title="SEC Analysis Report",
            height="900px",
            show_controls=True
        )

        return iframe_component, sec_url

    except Exception as e:
        print(f"❌ Error in load_sec_embed: {e}")
        import traceback
        traceback.print_exc()

        error_msg = f"Failed to load SEC application: {str(e)}"
        return create_error_iframe(error_msg), ""

# Test function to manually check SEC embedding
def test_sec_embed_url():
    """Test function to verify SEC URL generation"""
    test_report_id = "328"
    base_url = "/plotly_integration/dash-app/app/SecReportApp2/"
    test_url = f"{base_url}?report_id={test_report_id}"

    print(f"Test SEC URL: {test_url}")

    return dbc.Container([
        html.H3("SEC Embed Test"),
        html.P(f"Testing with report_id: {test_report_id}"),
        html.P(f"Generated URL: {test_url}", className="font-monospace"),
        html.Hr(),
        html.Iframe(
            src=test_url,
            style={"width": "100%", "height": "600px", "border": "1px solid #ddd"}
        )
    ], style={"padding": "20px"})