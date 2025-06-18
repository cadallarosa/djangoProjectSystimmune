# # SEC embedder component for integrating SecReportApp2 - Fixed duplicate outputs
#
# from dash import html, Input, Output, State, callback, no_update
# import dash_bootstrap_components as dbc
# from urllib.parse import parse_qs
# from ...shared.components.embedded_iframe import create_embedded_iframe, create_loading_iframe, create_error_iframe
# from ...shared.utils.url_helpers import build_sec_report_url
# from ...config.app_urls import get_app_url
#
#
# def create_embedded_sec_report(query_params):
#     """
#     Create embedded SEC report layout with parameters
#
#     Args:
#         query_params (dict): URL query parameters
#
#     Returns:
#         html.Div: Layout with embedded SEC report
#     """
#     # Extract parameters
#     sample_ids = query_params.get('samples', [''])[0].split(',') if query_params.get('samples') else []
#     report_id = query_params.get('report_id', [''])[0]
#     mode = query_params.get('mode', ['samples'])[0]
#
#     # Clean up sample IDs
#     sample_ids = [sid.strip() for sid in sample_ids if sid.strip()]
#
#     return dbc.Container([
#         # Header
#         dbc.Row([
#             dbc.Col([
#                 html.H2("SEC Analysis"),
#                 html.P(f"Size Exclusion Chromatography - {len(sample_ids)} samples selected" if sample_ids
#                        else "Size Exclusion Chromatography", className="text-muted")
#             ], md=8),
#             dbc.Col([
#                 dbc.ButtonGroup([
#                     dbc.Button([
#                         html.I(className="fas fa-arrow-left me-1"),
#                         "Back"
#                     ], href="/analysis/sec", color="outline-secondary", size="sm"),
#                     dbc.Button([
#                         html.I(className="fas fa-external-link-alt me-1"),
#                         "Open in New Tab"
#                     ], id="open-sec-new-tab", color="outline-primary", size="sm"),
#                     dbc.Button([
#                         html.I(className="fas fa-sync-alt me-1"),
#                         "Refresh"
#                     ], id="refresh-sec-report", color="outline-info", size="sm")
#                 ], className="float-end")
#             ], md=4)
#         ], className="mb-4"),
#
#         # Sample Information
#         dbc.Row([
#             dbc.Col([
#                 create_selected_samples_info(sample_ids, report_id)
#             ])
#         ], className="mb-3") if sample_ids or report_id else html.Div(),
#
#         # Embedded SEC Application
#         dbc.Row([
#             dbc.Col([
#                 html.Div(id="sec-embed-container")
#             ])
#         ])
#
#     ], fluid=True, style={"padding": "20px"})
#
#
# @callback(
#     [Output("sec-embed-container", "children"),  # ✅ REMOVED allow_duplicate - this is the main callback
#      Output("open-sec-new-tab", "href")],
#     [Input("url", "search"),
#      Input("refresh-sec-report", "n_clicks")],
#     [State("url", "pathname")]
# )
# def load_sec_embed(search, refresh_clicks, pathname):
#     """Load the embedded SEC application with parameters"""
#     if not pathname.startswith("/analysis/sec/report"):
#         return html.Div(), ""
#
#     try:
#         # Parse query parameters
#         query_params = parse_qs(search.lstrip('?')) if search else {}
#         sample_ids = query_params.get('samples', [''])[0].split(',') if query_params.get('samples') else []
#         report_id = query_params.get('report_id', [''])[0]
#         mode = query_params.get('mode', ['samples'])[0]
#
#         # Clean up sample IDs
#         sample_ids = [sid.strip() for sid in sample_ids if sid.strip()]
#
#         # Build SEC report URL
#         sec_url = build_sec_report_url(
#             sample_ids=sample_ids,
#             report_id=report_id,
#             mode=mode,
#             hide_report_tab=True
#         )
#
#         # Create embedded iframe
#         iframe_component = create_embedded_iframe(
#             src_url=sec_url,
#             title="SEC Analysis Report",
#             height="900px",
#             show_controls=True
#         )
#
#         return iframe_component, sec_url
#
#     except Exception as e:
#         error_msg = f"Failed to load SEC application: {str(e)}"
#         return create_error_iframe(error_msg), ""
#
#
# def create_selected_samples_info(sample_ids, report_id=None):
#     """Create information panel showing selected samples or report"""
#     if report_id:
#         return dbc.Alert([
#             html.I(className="fas fa-file-alt me-2"),
#             f"Viewing SEC Report ID: {report_id}"
#         ], color="info")
#
#     elif sample_ids:
#         # Show sample information
#         if len(sample_ids) <= 10:
#             sample_list = ", ".join(sample_ids)
#         else:
#             sample_list = f"{', '.join(sample_ids[:10])}... (+{len(sample_ids) - 10} more)"
#
#         return dbc.Alert([
#             html.I(className="fas fa-vial me-2"),
#             html.Strong(f"Selected Samples ({len(sample_ids)}): "),
#             sample_list
#         ], color="primary")
#
#     else:
#         return dbc.Alert([
#             html.I(className="fas fa-info-circle me-2"),
#             "No samples selected. Choose samples from the SEC dashboard to begin analysis."
#         ], color="warning")
#
#
# def create_sec_embed_error_handler():
#     """Create error handling for SEC embedding"""
#     return html.Div([
#         dbc.Alert([
#             html.H5("SEC Application Error", className="alert-heading"),
#             html.P("The SEC analysis application failed to load. This could be due to:"),
#             html.Ul([
#                 html.Li("The SEC application is not running"),
#                 html.Li("Network connectivity issues"),
#                 html.Li("Invalid sample parameters")
#             ]),
#             html.Hr(),
#             dbc.Button([
#                 html.I(className="fas fa-redo me-1"),
#                 "Retry Loading"
#             ], id="retry-sec-embed", color="primary"),
#             dbc.Button([
#                 html.I(className="fas fa-external-link-alt me-1"),
#                 "Open SEC App Directly"
#             ], href="/plotly_integration/dash-app/app/SecReportApp2/",
#                 target="_blank", color="outline-primary", className="ms-2")
#         ], color="danger")
#     ])
#
#
# @callback(
#     Output("sec-embed-container", "children", allow_duplicate=True),  # ✅ FIXED: Added allow_duplicate and prevent_initial_call
#     Input("retry-sec-embed", "n_clicks"),
#     [State("url", "search")],
#     prevent_initial_call=True  # ✅ REQUIRED for allow_duplicate
# )
# def retry_sec_embed(n_clicks, search):
#     """Retry loading SEC embed on error"""
#     if not n_clicks:
#         return no_update
#
#     # Show loading state
#     return create_loading_iframe("Retrying SEC Application...", "900px")
#
#
# def create_sec_embed_with_samples(sample_ids, mode="samples"):
#     """
#     Create SEC embed with specific samples
#
#     Args:
#         sample_ids (list): List of sample IDs
#         mode (str): Analysis mode
#
#     Returns:
#         html.Div: SEC embed component
#     """
#     sec_url = build_sec_report_url(
#         sample_ids=sample_ids,
#         mode=mode,
#         hide_report_tab=True
#     )
#
#     return html.Div([
#         create_selected_samples_info(sample_ids),
#         create_embedded_iframe(
#             src_url=sec_url,
#             title=f"SEC Analysis - {len(sample_ids)} Samples",
#             height="900px"
#         )
#     ])
#
#
# def create_sec_embed_with_report(report_id):
#     """
#     Create SEC embed with specific report
#
#     Args:
#         report_id (str): Report ID to view
#
#     Returns:
#         html.Div: SEC embed component
#     """
#     sec_url = build_sec_report_url(
#         report_id=report_id,
#         mode="report"
#     )
#
#     return html.Div([
#         create_selected_samples_info([], report_id),
#         create_embedded_iframe(
#             src_url=sec_url,
#             title=f"SEC Report {report_id}",
#             height="900px"
#         )
#     ])
#
#
# # Callback for iframe refresh functionality
# @callback(
#     Output({"type": "embedded-iframe", "index": "SEC Analysis Report"}, "src"),
#     Input({"type": "iframe-refresh", "index": "SEC Analysis Report"}, "n_clicks"),
#     [State({"type": "embedded-iframe", "index": "SEC Analysis Report"}, "src")],
#     prevent_initial_call=True
# )
# def refresh_sec_iframe(n_clicks, current_src):
#     """Refresh the SEC iframe"""
#     if not n_clicks or not current_src:
#         return no_update
#
#     # Add timestamp to force refresh
#     from datetime import datetime
#     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#     separator = "&" if "?" in current_src else "?"
#
#     return f"{current_src}{separator}_refresh={timestamp}"