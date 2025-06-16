# # from dash import html, dcc, dash_table, Input, Output, State, callback
# # from django_plotly_dash import DjangoDash
# # import dash_bootstrap_components as dbc
# # from plotly_integration.models import LimsUpstreamSamples, Report, LimsSecResult
# # from datetime import datetime, timedelta
# # from collections import defaultdict
# # import json
# #
# # # Create the Dash app
# # app = DjangoDash(
# #     "CLDDashboardApp",
# #     external_stylesheets=[
# #         dbc.themes.BOOTSTRAP,
# #         "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
# #     ],
# #     title="CLD Analytics Dashboard"
# # )
# #
# # # ================== TABLE CONFIGURATIONS ==================
# # # Table styling
# # TABLE_STYLE_CELL = {
# #     'textAlign': 'left',
# #     'fontSize': '11px',
# #     'fontFamily': 'Arial, sans-serif',
# #     'padding': '8px',
# #     'border': '1px solid #ddd'
# # }
# #
# # TABLE_STYLE_HEADER = {
# #     'backgroundColor': '#f8f9fa',
# #     'fontWeight': 'bold',
# #     'fontSize': '11px',
# #     'textAlign': 'center',
# #     'border': '1px solid #ddd',
# #     'color': '#495057'
# # }
# #
# # # FB Sample Fields
# # FB_SAMPLE_FIELDS = [
# #     {"name": "Sample #", "id": "sample_number", "editable": True},
# #     {"name": "Project", "id": "project_id", "editable": False},
# #     {"name": "Clone", "id": "cell_line", "editable": True},
# #     {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
# #     {"name": "Development Stage", "id": "development_stage", "editable": False},
# #     {"name": "Titer (mg/L)", "id": "titer", "editable": True, "type": "numeric"},
# #     {"name": "Volume (mL)", "id": "volume", "editable": True, "type": "numeric"},
# #     {"name": "SIP #", "id": "sip_number", "editable": False},
# #     {"name": "CLD Analyst", "id": "cld_analyst", "editable": False},
# #     {"name": "SEC Status", "id": "sec_status", "editable": False},
# #     {"name": "Actions", "id": "actions", "editable": False, "presentation": "markdown"}
# # ]
# #
# # # Sample Set Analytics Columns
# # SAMPLE_SET_ANALYTICS_COLUMNS = [
# #     {"name": "Project", "id": "project"},
# #     {"name": "Sample Range", "id": "range"},
# #     {"name": "SIP #", "id": "sip"},
# #     {"name": "Development Stage", "id": "development_stage"},
# #     {"name": "Sample Count", "id": "count"},
# #     {"name": "SEC Status", "id": "sec_status"},
# #     {"name": "Create SEC Report", "id": "create_sec", "presentation": "markdown"}
# # ]
# #
# # # ================== LAYOUT STYLES ==================
# # SIDEBAR_STYLE = {
# #     "position": "fixed",
# #     "top": 0,
# #     "left": 0,
# #     "bottom": 0,
# #     "width": "250px",
# #     "padding": "20px",
# #     "backgroundColor": "#f8f9fa",
# #     "borderRight": "1px solid #dee2e6",
# #     "overflowY": "auto",
# #     "zIndex": 1000
# # }
# #
# # CONTENT_STYLE = {
# #     "marginLeft": "260px",
# #     "marginRight": "10px",
# #     "padding": "0px"
# # }
# #
# # # ================== HELPER FUNCTIONS ==================
# # def get_dashboard_stats():
# #     """Get statistics for dashboard cards"""
# #     try:
# #         # FB samples have sample_type=2
# #         total_fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2).count()
# #
# #         # Recent samples (last 30 days)
# #         thirty_days_ago = datetime.now() - timedelta(days=30)
# #         recent_samples = LimsUpstreamSamples.objects.filter(
# #             sample_type=2,
# #             created_at__gte=thirty_days_ago
# #         ).count() if hasattr(LimsUpstreamSamples, 'created_at') else 0
# #
# #         # SEC Reports count
# #         sec_reports = Report.objects.filter(analysis_type=1).count()
# #
# #         # Pending analyses count
# #         pending_analyses = max(0, total_fb_samples - sec_reports)
# #
# #         return {
# #             'total_samples': total_fb_samples,
# #             'recent_samples': recent_samples,
# #             'sec_reports': sec_reports,
# #             'pending_analyses': pending_analyses
# #         }
# #     except Exception as e:
# #         print(f"Error getting dashboard stats: {e}")
# #         return {
# #             'total_samples': 0,
# #             'recent_samples': 0,
# #             'sec_reports': 0,
# #             'pending_analyses': 0
# #         }
# #
# # def get_sample_sets_with_analytics():
# #     """Get sample sets and their analytics status"""
# #     try:
# #         # Get FB samples and group them
# #         fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2)
# #         grouped = defaultdict(list)
# #
# #         for sample in fb_samples:
# #             key = (sample.project, sample.sip_number, sample.development_stage)
# #             grouped[key].append(sample.sample_number)
# #
# #         # Check SEC status for each set
# #         table_data = []
# #         for (project, sip, dev_stage), sample_nums in grouped.items():
# #             if not sample_nums:
# #                 continue
# #
# #             sorted_nums = sorted(sample_nums)
# #             sample_ids = [f"FB{n}" for n in sorted_nums]
# #             sample_range = f"FB{sorted_nums[0]} to FB{sorted_nums[-1]}"
# #
# #             # Check if samples have SEC results
# #             # This is a simplified check - you may need to adjust based on your data structure
# #             sec_reports = Report.objects.filter(
# #                 analysis_type=1,
# #                 sample_type="FB",
# #                 project_id=project
# #             ).count()
# #
# #             sec_status = "✅ Complete" if sec_reports > 0 else "⚠️ Pending"
# #
# #             # Create SEC report button with sample set parameters
# #             sample_set_data = {
# #                 "project": project,
# #                 "sip": sip,
# #                 "development_stage": dev_stage,
# #                 "sample_ids": sample_ids
# #             }
# #
# #             # Encode sample set data for URL
# #             encoded_data = json.dumps(sample_set_data).replace('"', '%22').replace(' ', '%20')
# #             create_sec_link = f"[📊 Create SEC Report](/plotly_integration/dash-app/app/SecReportApp2/?sample_set={encoded_data})"
# #
# #             table_data.append({
# #                 "project": project or "",
# #                 "sip": sip or "",
# #                 "development_stage": dev_stage or "",
# #                 "range": sample_range,
# #                 "count": len(sample_ids),
# #                 "sec_status": sec_status,
# #                 "create_sec": create_sec_link,
# #                 "sample_ids": sample_ids  # Store for internal use
# #             })
# #
# #         return table_data
# #     except Exception as e:
# #         print(f"Error getting sample sets: {e}")
# #         return []
# #
# # def create_stats_card(title, value, subtitle, color, icon):
# #     """Create a statistics card"""
# #     return dbc.Card([
# #         dbc.CardBody([
# #             html.Div([
# #                 html.Div([
# #                     html.H3(str(value), className="text-primary mb-0"),
# #                     html.P(title, className="text-muted mb-0"),
# #                     html.Small(subtitle, className="text-muted")
# #                 ], className="flex-grow-1"),
# #                 html.Div([
# #                     html.I(className=f"fas {icon} fa-2x text-{color}")
# #                 ], className="align-self-center")
# #             ], className="d-flex")
# #         ])
# #     ], className="shadow-sm h-100")
# #
# # # ================== LAYOUT COMPONENTS ==================
# # def get_sidebar():
# #     """Create the sidebar navigation"""
# #     return html.Div([
# #         html.H4("🧬 CLD Analytics", className="text-primary mb-3"),
# #         html.Hr(),
# #
# #         dbc.Nav([
# #             # Dashboard
# #             dbc.NavLink([
# #                 html.I(className="fas fa-tachometer-alt me-2"),
# #                 "Dashboard"
# #             ], href="/", active="exact"),
# #
# #             html.Hr(className="my-2"),
# #
# #             # FB Samples section
# #             html.P("SAMPLE MANAGEMENT", className="text-muted small fw-bold mb-1"),
# #             dbc.NavLink([
# #                 html.I(className="fas fa-vial me-2"),
# #                 "View All Samples"
# #             ], href="/fb-samples/view", active="exact"),
# #             dbc.NavLink([
# #                 html.I(className="fas fa-layer-group me-2"),
# #                 "Sample Sets"
# #             ], href="/fb-samples/sets", active="exact"),
# #             dbc.NavLink([
# #                 html.I(className="fas fa-plus me-2"),
# #                 "Add Samples"
# #             ], href="/fb-samples/create", active="exact"),
# #
# #             html.Hr(className="my-2"),
# #
# #             # Analytics section
# #             html.P("ANALYTICS", className="text-muted small fw-bold mb-1"),
# #             dbc.NavLink([
# #                 html.I(className="fas fa-chart-bar me-2"),
# #                 "Sample Set Analytics"
# #             ], href="/analytics/sample-sets", active="exact"),
# #             dbc.NavLink([
# #                 html.I(className="fas fa-chart-line me-2"),
# #                 "View SEC Reports"
# #             ], href="/reports/sec/view", active="exact"),
# #             dbc.NavLink([
# #                 html.I(className="fas fa-plus-circle me-2"),
# #                 "Create SEC Report"
# #             ], href="/reports/sec/create", active="exact"),
# #
# #             html.Hr(className="my-2"),
# #
# #             # Settings
# #             html.P("SYSTEM", className="text-muted small fw-bold mb-1"),
# #             dbc.NavLink([
# #                 html.I(className="fas fa-calendar-check me-2"),
# #                 "Calibrations"
# #             ], href="/analytics/calibrations", active="exact"),
# #             dbc.NavLink([
# #                 html.I(className="fas fa-cogs me-2"),
# #                 "Settings"
# #             ], href="/settings", active="exact")
# #
# #         ], vertical=True, pills=True)
# #     ], style=SIDEBAR_STYLE)
# #
# # def dashboard_overview_layout():
# #     """Main dashboard overview layout"""
# #     stats = get_dashboard_stats()
# #
# #     return html.Div([
# #         # Header
# #         dbc.Row([
# #             dbc.Col([
# #                 html.H2("🧬 CLD Analytics Dashboard", className="text-primary mb-1"),
# #                 html.P("Cell Line Development - FB Sample Management & Analytics",
# #                       className="text-muted mb-4")
# #             ])
# #         ]),
# #
# #         # Statistics Cards
# #         dbc.Row([
# #             dbc.Col([
# #                 create_stats_card(
# #                     "Total FB Samples",
# #                     stats['total_samples'],
# #                     "All time",
# #                     "primary",
# #                     "fa-vial"
# #                 )
# #             ], md=3),
# #             dbc.Col([
# #                 create_stats_card(
# #                     "Recent Samples",
# #                     stats['recent_samples'],
# #                     "Last 30 days",
# #                     "success",
# #                     "fa-plus-circle"
# #                 )
# #             ], md=3),
# #             dbc.Col([
# #                 create_stats_card(
# #                     "SEC Reports",
# #                     stats['sec_reports'],
# #                     "Generated",
# #                     "info",
# #                     "fa-chart-line"
# #                 )
# #             ], md=3),
# #             dbc.Col([
# #                 create_stats_card(
# #                     "Pending Analyses",
# #                     stats['pending_analyses'],
# #                     "Awaiting analysis",
# #                     "warning",
# #                     "fa-clock"
# #                 )
# #             ], md=3)
# #         ], className="mb-4"),
# #
# #         # Quick Actions
# #         dbc.Row([
# #             dbc.Col([
# #                 dbc.Card([
# #                     dbc.CardHeader([
# #                         html.H5("⚡ Quick Actions", className="mb-0")
# #                     ]),
# #                     dbc.CardBody([
# #                         dbc.Row([
# #                             dbc.Col([
# #                                 dbc.Button([
# #                                     html.I(className="fas fa-chart-bar me-2"),
# #                                     "Sample Set Analytics"
# #                                 ], color="primary", href="/analytics/sample-sets", size="lg",
# #                                 className="w-100 mb-2")
# #                             ], md=6),
# #                             dbc.Col([
# #                                 dbc.Button([
# #                                     html.I(className="fas fa-search me-2"),
# #                                     "View All Samples"
# #                                 ], color="outline-primary", href="/fb-samples/view",
# #                                 size="lg", className="w-100 mb-2")
# #                             ], md=6),
# #                             dbc.Col([
# #                                 dbc.Button([
# #                                     html.I(className="fas fa-plus me-2"),
# #                                     "Add FB Samples"
# #                                 ], color="success", href="/fb-samples/create",
# #                                 size="lg", className="w-100 mb-2")
# #                             ], md=6),
# #                             dbc.Col([
# #                                 dbc.Button([
# #                                     html.I(className="fas fa-history me-2"),
# #                                     "View Reports"
# #                                 ], color="outline-success", href="/reports/sec/view",
# #                                 size="lg", className="w-100 mb-2")
# #                             ], md=6)
# #                         ])
# #                     ])
# #                 ])
# #             ], md=8),
# #
# #             # Recent Activity
# #             dbc.Col([
# #                 dbc.Card([
# #                     dbc.CardHeader([
# #                         html.H5("📈 Recent Activity", className="mb-0")
# #                     ]),
# #                     dbc.CardBody([
# #                         html.Div(id="recent-activity-feed", children=[
# #                             html.P("✅ Dashboard ready", className="small mb-1"),
# #                             html.P("📊 Analytics available", className="small mb-1"),
# #                             html.P("🧪 FB samples loaded", className="small mb-1"),
# #                             html.P("⚙️ System operational", className="small mb-0"),
# #                         ])
# #                     ])
# #                 ])
# #             ], md=4)
# #         ])
# #     ], style={"padding": "20px"})
# #
# # def sample_set_analytics_layout():
# #     """Sample Set Analytics layout - NEW"""
# #     return html.Div([
# #         # Header
# #         dbc.Row([
# #             dbc.Col([
# #                 html.H3("📊 Sample Set Analytics", className="text-primary mb-1"),
# #                 html.P("Select sample sets for analysis. Each set contains samples grouped by project, SIP, and development stage.",
# #                       className="text-muted")
# #             ], md=8),
# #             dbc.Col([
# #                 dbc.Button([
# #                     html.I(className="fas fa-sync me-1"),
# #                     "Refresh"
# #                 ], id="refresh-sample-sets-btn", color="outline-primary", size="sm")
# #             ], md=4, className="text-end")
# #         ], className="mb-3"),
# #
# #         # Instructions Card
# #         dbc.Card([
# #             dbc.CardBody([
# #                 html.H6("📋 How to create analytics:", className="text-primary mb-2"),
# #                 html.Ol([
# #                     html.Li("Review the sample sets below"),
# #                     html.Li("Click 'Create SEC Report' for the desired sample set"),
# #                     html.Li("The SEC report app will open with all samples from that set pre-loaded"),
# #                     html.Li("Complete the analysis and save the report")
# #                 ], className="mb-0 small")
# #             ])
# #         ], className="mb-4"),
# #
# #         # Sample Sets Table
# #         dash_table.DataTable(
# #             id="sample-sets-analytics-table",
# #             columns=SAMPLE_SET_ANALYTICS_COLUMNS,
# #             data=[],
# #             filter_action="native",
# #             sort_action="native",
# #             page_action="native",
# #             page_size=25,
# #             style_cell=TABLE_STYLE_CELL,
# #             style_header=TABLE_STYLE_HEADER,
# #             style_data_conditional=[
# #                 {
# #                     "if": {
# #                         "filter_query": '{sec_status} contains "Complete"'
# #                     },
# #                     "backgroundColor": "#d4edda",
# #                     "color": "#155724"
# #                 },
# #                 {
# #                     "if": {
# #                         "filter_query": '{sec_status} contains "Pending"'
# #                     },
# #                     "backgroundColor": "#fff3cd",
# #                     "color": "#856404"
# #                 }
# #             ],
# #             markdown_options={"link_target": "_blank"}
# #         ),
# #
# #         # Status
# #         html.Div(id="sample-sets-analytics-status", className="text-muted small mt-2")
# #     ], style={"padding": "20px"})
# #
# # def fb_samples_view_layout():
# #     """FB samples view layout"""
# #     return html.Div([
# #         # Header with actions
# #         dbc.Row([
# #             dbc.Col([
# #                 html.H3("🧪 All FB Samples", className="text-primary mb-1"),
# #                 html.P("Complete list of Cell Line Development samples", className="text-muted")
# #             ], md=8),
# #             dbc.Col([
# #                 dbc.ButtonGroup([
# #                     dbc.Button([
# #                         html.I(className="fas fa-sync me-1"),
# #                         "Refresh"
# #                     ], id="refresh-samples-btn", color="outline-primary", size="sm"),
# #                     dbc.Button([
# #                         html.I(className="fas fa-plus me-1"),
# #                         "Add Samples"
# #                     ], href="/fb-samples/create", color="primary", size="sm"),
# #                     dbc.Button([
# #                         html.I(className="fas fa-download me-1"),
# #                         "Export"
# #                     ], id="export-samples-btn", color="outline-secondary", size="sm")
# #                 ])
# #             ], md=4, className="text-end")
# #         ], className="mb-3"),
# #
# #         # Main Data Table
# #         dash_table.DataTable(
# #             id="fb-samples-table",
# #             columns=[
# #                 {
# #                     "name": col["name"],
# #                     "id": col["id"],
# #                     "editable": col.get("editable", False),
# #                     "type": col.get("type", "text"),
# #                     "presentation": col.get("presentation", "input")
# #                 } for col in FB_SAMPLE_FIELDS
# #             ],
# #             data=[],
# #             editable=True,
# #             sort_action="native",
# #             filter_action="native",
# #             page_action="native",
# #             page_size=25,
# #             row_selectable="multi",
# #             selected_rows=[],
# #             style_cell=TABLE_STYLE_CELL,
# #             style_header=TABLE_STYLE_HEADER
# #         ),
# #
# #         # Status
# #         html.Div(id="fb-samples-status", className="text-muted small mt-2")
# #     ], style={"padding": "20px"})
# #
# # # [Keep all other existing layout functions - fb_samples_create_layout, sec_reports_create_layout, etc.]
# #
# # # ================== MAIN APP LAYOUT ==================
# # app.layout = html.Div([
# #     dcc.Location(id="url"),
# #     get_sidebar(),
# #     html.Div(id="page-content", style=CONTENT_STYLE)
# # ])
# #
# # # ================== CALLBACKS ==================
# # # Main page routing
# # @app.callback(
# #     Output("page-content", "children"),
# #     Input("url", "pathname")
# # )
# # def display_page(pathname):
# #     """Route pages based on URL pathname"""
# #     if pathname == "/" or pathname == "/dashboard":
# #         return dashboard_overview_layout()
# #     elif pathname == "/fb-samples/view":
# #         return fb_samples_view_layout()
# #     elif pathname == "/analytics/sample-sets":  # NEW
# #         return sample_set_analytics_layout()
# #     elif pathname == "/fb-samples/create":
# #         return fb_samples_create_layout()  # Keep existing
# #     elif pathname == "/reports/sec/create":
# #         return sec_reports_create_layout()  # Keep existing
# #     elif pathname == "/reports/sec/view":
# #         return sec_reports_view_layout()  # Keep existing
# #     else:
# #         return html.Div([
# #             dbc.Alert([
# #                 html.H4("404 - Page Not Found", className="alert-heading"),
# #                 html.P("The page you're looking for doesn't exist."),
# #                 html.Hr(),
# #                 dbc.Button("Go to Dashboard", href="/", color="primary")
# #             ], color="warning")
# #         ], style={"padding": "50px"})
# #
# # # Load sample sets for analytics - NEW
# # @app.callback(
# #     Output("sample-sets-analytics-table", "data"),
# #     Output("sample-sets-analytics-status", "children"),
# #     [Input("refresh-sample-sets-btn", "n_clicks")],
# #     prevent_initial_call=False
# # )
# # def load_sample_sets_analytics(n_clicks):
# #     """Load sample sets for analytics"""
# #     try:
# #         data = get_sample_sets_with_analytics()
# #         status = f"📊 Loaded {len(data)} sample sets ready for analytics"
# #         return data, status
# #     except Exception as e:
# #         return [], f"❌ Error loading sample sets: {str(e)}"
# #
# # # [Keep all existing callbacks]
#
# from dash import html, dcc, dash_table, Input, Output, State, callback, ctx
# from django_plotly_dash import DjangoDash
# import dash_bootstrap_components as dbc
# from plotly_integration.models import LimsUpstreamSamples, Report, LimsSecResult, LimsSampleAnalysis, \
#     LimsProjectInformation
# from datetime import datetime, timedelta
# from collections import defaultdict
# import json
# from django.db.models import Max
# import dash
#
# # Create the Dash app
# app = DjangoDash(
#     "CLDDashboardApp2",
#     external_stylesheets=[
#         dbc.themes.BOOTSTRAP,
#         "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
#     ],
#     title="CLD Analytics Dashboard"
# )
#
# # ================== TABLE CONFIGURATIONS ==================
# # Table styling
# TABLE_STYLE_CELL = {
#     'textAlign': 'left',
#     'fontSize': '11px',
#     'fontFamily': 'Arial, sans-serif',
#     'padding': '8px',
#     'border': '1px solid #ddd'
# }
#
# TABLE_STYLE_HEADER = {
#     'backgroundColor': '#f8f9fa',
#     'fontWeight': 'bold',
#     'fontSize': '11px',
#     'textAlign': 'center',
#     'border': '1px solid #ddd',
#     'color': '#495057'
# }
#
# # FB Sample Fields
# FB_SAMPLE_FIELDS = [
#     {"name": "Sample #", "id": "sample_number", "editable": False},
#     {"name": "Project", "id": "project", "editable": False},
#     {"name": "Clone", "id": "cell_line", "editable": True},
#     {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
#     {"name": "Development Stage", "id": "development_stage", "editable": True},
#     {"name": "Titer (mg/L)", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
#     {"name": "Volume (mL)", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
#     {"name": "SIP #", "id": "sip_number", "editable": True},
#     {"name": "CLD Analyst", "id": "analyst", "editable": True},
#     {"name": "SEC Status", "id": "sec_status", "editable": False},
#     {"name": "Actions", "id": "actions", "editable": False, "presentation": "markdown"}
# ]
#
# # Sample Set Analytics Columns
# SAMPLE_SET_ANALYTICS_COLUMNS = [
#     {"name": "Project", "id": "project"},
#     {"name": "Sample Range", "id": "range"},
#     {"name": "SIP #", "id": "sip"},
#     {"name": "Development Stage", "id": "development_stage"},
#     {"name": "Sample Count", "id": "count"},
#     {"name": "SEC Status", "id": "sec_status"},
#     {"name": "Create SEC Report", "id": "create_sec", "presentation": "markdown"}
# ]
#
# # SEC Report Columns
# SEC_COLUMNS = [
#     {"name": "Sample Name", "id": "sample_name"},
#     {"name": "Result ID", "id": "result_id"},
#     {"name": "Date Acquired", "id": "date_acquired"},
#     {"name": "Column Name", "id": "column_name"},
#     {"name": "Sample Set Name", "id": "sample_set_name"}
# ]
#
# # Fields configuration for editable fields
# EDITABLE_FIELDS = ["cell_line", "harvest_date", "development_stage", "hf_octet_titer",
#                    "hccf_loading_volume", "sip_number", "analyst", "pro_aqa_hf_titer",
#                    "pro_aqa_e_titer", "proa_eluate_a280_conc", "proa_eluate_volume", "note"]
#
# # ================== LAYOUT STYLES ==================
# SIDEBAR_STYLE = {
#     "position": "fixed",
#     "top": 0,
#     "left": 0,
#     "bottom": 0,
#     "width": "250px",
#     "padding": "20px",
#     "backgroundColor": "#f8f9fa",
#     "borderRight": "1px solid #dee2e6",
#     "overflowY": "auto",
#     "zIndex": 1000
# }
#
# CONTENT_STYLE = {
#     "marginLeft": "260px",
#     "marginRight": "10px",
#     "padding": "0px"
# }
#
#
# # ================== HELPER FUNCTIONS ==================
# def calculate_recoveries(sample):
#     """Calculate recovery percentages"""
#     fast_pro_a_recovery = None
#     a280_recovery = None
#
#     try:
#         if all([
#             sample.proa_eluate_volume is not None,
#             sample.pro_aqa_e_titer is not None,
#             sample.hccf_loading_volume is not None,
#             sample.pro_aqa_hf_titer is not None
#         ]):
#             fast_pro_a_recovery = (
#                                           sample.proa_eluate_volume * sample.pro_aqa_e_titer
#                                   ) / (
#                                           sample.hccf_loading_volume * sample.pro_aqa_hf_titer
#                                   ) * 100
#
#         if all([
#             sample.proa_eluate_volume is not None,
#             sample.proa_eluate_a280_conc is not None,
#             sample.hccf_loading_volume is not None,
#             sample.pro_aqa_hf_titer is not None
#         ]):
#             a280_recovery = (
#                                     sample.proa_eluate_volume * sample.proa_eluate_a280_conc
#                             ) / (
#                                     sample.hccf_loading_volume * sample.pro_aqa_hf_titer
#                             ) * 100
#     except ZeroDivisionError:
#         pass
#
#     return (
#         round(fast_pro_a_recovery, 1) if fast_pro_a_recovery is not None else None,
#         round(a280_recovery, 1) if a280_recovery is not None else None,
#     )
#
#
# def get_dashboard_stats():
#     """Get statistics for dashboard cards"""
#     try:
#         # FB samples have sample_type=2
#         total_fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2).count()
#
#         # Recent samples (last 30 days)
#         thirty_days_ago = datetime.now() - timedelta(days=30)
#         recent_samples = LimsUpstreamSamples.objects.filter(
#             sample_type=2,
#             created_at__gte=thirty_days_ago
#         ).count() if hasattr(LimsUpstreamSamples, 'created_at') else 0
#
#         # SEC Reports count
#         sec_reports = Report.objects.filter(analysis_type=1).count()
#
#         # Pending analyses count
#         pending_analyses = max(0, total_fb_samples - sec_reports)
#
#         return {
#             'total_samples': total_fb_samples,
#             'recent_samples': recent_samples,
#             'sec_reports': sec_reports,
#             'pending_analyses': pending_analyses
#         }
#     except Exception as e:
#         print(f"Error getting dashboard stats: {e}")
#         return {
#             'total_samples': 0,
#             'recent_samples': 0,
#             'sec_reports': 0,
#             'pending_analyses': 0
#         }
#
#
# def get_sample_sets_with_analytics():
#     """Get sample sets and their analytics status"""
#     try:
#         # Get FB samples and group them
#         fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2)
#         grouped = defaultdict(list)
#
#         for sample in fb_samples:
#             key = (sample.project, sample.sip_number, sample.development_stage)
#             grouped[key].append(sample.sample_number)
#
#         # Check SEC status for each set
#         table_data = []
#         for (project, sip, dev_stage), sample_nums in grouped.items():
#             if not sample_nums:
#                 continue
#
#             sorted_nums = sorted(sample_nums)
#             sample_ids = [f"FB{n}" for n in sorted_nums]
#             sample_range = f"FB{sorted_nums[0]} to FB{sorted_nums[-1]}"
#
#             # Check if samples have SEC results
#             sec_reports = Report.objects.filter(
#                 analysis_type=1,
#                 sample_type="FB",
#                 project_id=project
#             ).count()
#
#             sec_status = "✅ Complete" if sec_reports > 0 else "⚠️ Pending"
#
#             # Create SEC report button with sample set parameters
#             sample_set_data = {
#                 "project": project,
#                 "sip": sip,
#                 "development_stage": dev_stage,
#                 "sample_ids": sample_ids
#             }
#
#             # Encode sample set data for URL
#             encoded_data = json.dumps(sample_set_data).replace('"', '%22').replace(' ', '%20')
#             create_sec_link = f"[📊 Create SEC Report](/plotly_integration/dash-app/app/SecReportApp2/?sample_set={encoded_data})"
#
#             table_data.append({
#                 "project": project or "",
#                 "sip": sip or "",
#                 "development_stage": dev_stage or "",
#                 "range": sample_range,
#                 "count": len(sample_ids),
#                 "sec_status": sec_status,
#                 "create_sec": create_sec_link,
#                 "sample_ids": sample_ids  # Store for internal use
#             })
#
#         return table_data
#     except Exception as e:
#         print(f"Error getting sample sets: {e}")
#         return []
#
#
# def create_stats_card(title, value, subtitle, color, icon):
#     """Create a statistics card"""
#     return dbc.Card([
#         dbc.CardBody([
#             html.Div([
#                 html.Div([
#                     html.H3(str(value), className="text-primary mb-0"),
#                     html.P(title, className="text-muted mb-0"),
#                     html.Small(subtitle, className="text-muted")
#                 ], className="flex-grow-1"),
#                 html.Div([
#                     html.I(className=f"fas {icon} fa-2x text-{color}")
#                 ], className="align-self-center")
#             ], className="d-flex")
#         ])
#     ], className="shadow-sm h-100")
#
#
# # ================== LAYOUT COMPONENTS ==================
# def get_sidebar():
#     """Create the sidebar navigation"""
#     return html.Div([
#         html.H4("🧬 CLD Analytics", className="text-primary mb-3"),
#         html.Hr(),
#
#         dbc.Nav([
#             # Dashboard
#             dbc.NavLink([
#                 html.I(className="fas fa-tachometer-alt me-2"),
#                 "Dashboard"
#             ], href="/", active="exact"),
#
#             html.Hr(className="my-2"),
#
#             # FB Samples section
#             html.P("SAMPLE MANAGEMENT", className="text-muted small fw-bold mb-1"),
#             dbc.NavLink([
#                 html.I(className="fas fa-vial me-2"),
#                 "View All Samples"
#             ], href="/fb-samples/view", active="exact"),
#             dbc.NavLink([
#                 html.I(className="fas fa-layer-group me-2"),
#                 "Sample Sets"
#             ], href="/fb-samples/sets", active="exact"),
#             dbc.NavLink([
#                 html.I(className="fas fa-plus me-2"),
#                 "Add Samples"
#             ], href="/fb-samples/create", active="exact"),
#
#             html.Hr(className="my-2"),
#
#             # Analytics section
#             html.P("ANALYTICS", className="text-muted small fw-bold mb-1"),
#             dbc.NavLink([
#                 html.I(className="fas fa-chart-bar me-2"),
#                 "Sample Set Analytics"
#             ], href="/analytics/sample-sets", active="exact"),
#             dbc.NavLink([
#                 html.I(className="fas fa-chart-line me-2"),
#                 "View SEC Reports"
#             ], href="/reports/sec/view", active="exact"),
#             dbc.NavLink([
#                 html.I(className="fas fa-plus-circle me-2"),
#                 "Create SEC Report"
#             ], href="/reports/sec/create", active="exact"),
#
#             html.Hr(className="my-2"),
#
#             # Settings
#             html.P("SYSTEM", className="text-muted small fw-bold mb-1"),
#             dbc.NavLink([
#                 html.I(className="fas fa-calendar-check me-2"),
#                 "Calibrations"
#             ], href="/analytics/calibrations", active="exact"),
#             dbc.NavLink([
#                 html.I(className="fas fa-cogs me-2"),
#                 "Settings"
#             ], href="/settings", active="exact")
#
#         ], vertical=True, pills=True)
#     ], style=SIDEBAR_STYLE)
#
#
# def dashboard_overview_layout():
#     """Main dashboard overview layout"""
#     stats = get_dashboard_stats()
#
#     return html.Div([
#         # Header
#         dbc.Row([
#             dbc.Col([
#                 html.H2("🧬 CLD Analytics Dashboard", className="text-primary mb-1"),
#                 html.P("Cell Line Development - FB Sample Management & Analytics",
#                        className="text-muted mb-4")
#             ])
#         ]),
#
#         # Statistics Cards
#         dbc.Row([
#             dbc.Col([
#                 create_stats_card(
#                     "Total FB Samples",
#                     stats['total_samples'],
#                     "All time",
#                     "primary",
#                     "fa-vial"
#                 )
#             ], md=3),
#             dbc.Col([
#                 create_stats_card(
#                     "Recent Samples",
#                     stats['recent_samples'],
#                     "Last 30 days",
#                     "success",
#                     "fa-plus-circle"
#                 )
#             ], md=3),
#             dbc.Col([
#                 create_stats_card(
#                     "SEC Reports",
#                     stats['sec_reports'],
#                     "Generated",
#                     "info",
#                     "fa-chart-line"
#                 )
#             ], md=3),
#             dbc.Col([
#                 create_stats_card(
#                     "Pending Analyses",
#                     stats['pending_analyses'],
#                     "Awaiting analysis",
#                     "warning",
#                     "fa-clock"
#                 )
#             ], md=3)
#         ], className="mb-4"),
#
#         # Quick Actions
#         dbc.Row([
#             dbc.Col([
#                 dbc.Card([
#                     dbc.CardHeader([
#                         html.H5("⚡ Quick Actions", className="mb-0")
#                     ]),
#                     dbc.CardBody([
#                         dbc.Row([
#                             dbc.Col([
#                                 dbc.Button([
#                                     html.I(className="fas fa-chart-bar me-2"),
#                                     "Sample Set Analytics"
#                                 ], color="primary", href="/analytics/sample-sets", size="lg",
#                                     className="w-100 mb-2")
#                             ], md=6),
#                             dbc.Col([
#                                 dbc.Button([
#                                     html.I(className="fas fa-search me-2"),
#                                     "View All Samples"
#                                 ], color="outline-primary", href="/fb-samples/view",
#                                     size="lg", className="w-100 mb-2")
#                             ], md=6),
#                             dbc.Col([
#                                 dbc.Button([
#                                     html.I(className="fas fa-plus me-2"),
#                                     "Add FB Samples"
#                                 ], color="success", href="/fb-samples/create",
#                                     size="lg", className="w-100 mb-2")
#                             ], md=6),
#                             dbc.Col([
#                                 dbc.Button([
#                                     html.I(className="fas fa-history me-2"),
#                                     "View Reports"
#                                 ], color="outline-success", href="/reports/sec/view",
#                                     size="lg", className="w-100 mb-2")
#                             ], md=6)
#                         ])
#                     ])
#                 ])
#             ], md=8),
#
#             # Recent Activity
#             dbc.Col([
#                 dbc.Card([
#                     dbc.CardHeader([
#                         html.H5("📈 Recent Activity", className="mb-0")
#                     ]),
#                     dbc.CardBody([
#                         html.Div(id="recent-activity-feed", children=[
#                             html.P("✅ Dashboard ready", className="small mb-1"),
#                             html.P("📊 Analytics available", className="small mb-1"),
#                             html.P("🧪 FB samples loaded", className="small mb-1"),
#                             html.P("⚙️ System operational", className="small mb-0"),
#                         ])
#                     ])
#                 ])
#             ], md=4)
#         ])
#     ], style={"padding": "20px"})
#
#
# def sample_set_analytics_layout():
#     """Sample Set Analytics layout"""
#     return html.Div([
#         # Header
#         dbc.Row([
#             dbc.Col([
#                 html.H3("📊 Sample Set Analytics", className="text-primary mb-1"),
#                 html.P(
#                     "Select sample sets for analysis. Each set contains samples grouped by project, SIP, and development stage.",
#                     className="text-muted")
#             ], md=8),
#             dbc.Col([
#                 dbc.Button([
#                     html.I(className="fas fa-sync me-1"),
#                     "Refresh"
#                 ], id="refresh-sample-sets-btn", color="outline-primary", size="sm")
#             ], md=4, className="text-end")
#         ], className="mb-3"),
#
#         # Instructions Card
#         dbc.Card([
#             dbc.CardBody([
#                 html.H6("📋 How to create analytics:", className="text-primary mb-2"),
#                 html.Ol([
#                     html.Li("Review the sample sets below"),
#                     html.Li("Click 'Create SEC Report' for the desired sample set"),
#                     html.Li("The SEC report app will open with all samples from that set pre-loaded"),
#                     html.Li("Complete the analysis and save the report")
#                 ], className="mb-0 small")
#             ])
#         ], className="mb-4"),
#
#         # Sample Sets Table
#         dash_table.DataTable(
#             id="sample-sets-analytics-table",
#             columns=SAMPLE_SET_ANALYTICS_COLUMNS,
#             data=[],
#             filter_action="native",
#             sort_action="native",
#             page_action="native",
#             page_size=25,
#             style_cell=TABLE_STYLE_CELL,
#             style_header=TABLE_STYLE_HEADER,
#             style_data_conditional=[
#                 {
#                     "if": {
#                         "filter_query": '{sec_status} contains "Complete"'
#                     },
#                     "backgroundColor": "#d4edda",
#                     "color": "#155724"
#                 },
#                 {
#                     "if": {
#                         "filter_query": '{sec_status} contains "Pending"'
#                     },
#                     "backgroundColor": "#fff3cd",
#                     "color": "#856404"
#                 }
#             ],
#             markdown_options={"link_target": "_blank"}
#         ),
#
#         # Status
#         html.Div(id="sample-sets-analytics-status", className="text-muted small mt-2")
#     ], style={"padding": "20px"})
#
#
# def fb_samples_view_layout():
#     """FB samples view layout with all samples"""
#     return html.Div([
#         # Header with actions
#         dbc.Row([
#             dbc.Col([
#                 html.H3("🧪 All FB Samples", className="text-primary mb-1"),
#                 html.P("Complete list of Cell Line Development samples", className="text-muted")
#             ], md=8),
#             dbc.Col([
#                 dbc.ButtonGroup([
#                     dbc.Button([
#                         html.I(className="fas fa-sync me-1"),
#                         "Refresh"
#                     ], id="refresh-samples-btn", color="outline-primary", size="sm"),
#                     dbc.Button([
#                         html.I(className="fas fa-save me-1"),
#                         "Save Changes"
#                     ], id="save-samples-btn", color="primary", size="sm"),
#                     dbc.Button([
#                         html.I(className="fas fa-plus me-1"),
#                         "Add Samples"
#                     ], href="/fb-samples/create", color="success", size="sm"),
#                     dbc.Button([
#                         html.I(className="fas fa-download me-1"),
#                         "Export"
#                     ], id="export-samples-btn", color="outline-secondary", size="sm")
#                 ])
#             ], md=4, className="text-end")
#         ], className="mb-3"),
#
#         # Main Data Table with extended fields
#         dash_table.DataTable(
#             id="fb-samples-table",
#             columns=[
#                 {"name": "Sample #", "id": "sample_number", "editable": False},
#                 {"name": "Project", "id": "project", "editable": False},
#                 {"name": "Clone", "id": "cell_line", "editable": True},
#                 {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
#                 {"name": "Dev Stage", "id": "development_stage", "editable": True},
#                 {"name": "SIP #", "id": "sip_number", "editable": True},
#                 {"name": "Analyst", "id": "analyst", "editable": True},
#                 {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
#                 {"name": "ProAqa HF", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
#                 {"name": "ProAqa E", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
#                 {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
#                 {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
#                 {"name": "Eluate Vol", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
#                 {"name": "ProAqa Rec %", "id": "fast_pro_a_recovery", "editable": False, "type": "numeric"},
#                 {"name": "A280 Rec %", "id": "purification_recovery_a280", "editable": False, "type": "numeric"},
#                 {"name": "Note", "id": "note", "editable": True},
#                 {"name": "Report", "id": "report_link", "editable": False, "presentation": "markdown"}
#             ],
#             data=[],
#             editable=True,
#             sort_action="native",
#             filter_action="native",
#             page_action="native",
#             page_size=25,
#             row_selectable="multi",
#             selected_rows=[],
#             style_cell=TABLE_STYLE_CELL,
#             style_header=TABLE_STYLE_HEADER,
#             markdown_options={"link_target": "_blank"}
#         ),
#
#         # Status
#         html.Div(id="fb-samples-status", className="text-muted small mt-2")
#     ], style={"padding": "20px"})
#
#
# def fb_samples_create_layout():
#     """Create new FB samples layout"""
#     return html.Div([
#         html.H3("➕ Create New FB Samples", className="text-primary mb-4"),
#
#         # Form fields
#         dbc.Row([
#             dbc.Col([
#                 dbc.Label("Project:"),
#                 dcc.Dropdown(
#                     id="create-project-dropdown",
#                     placeholder="Select protein - molecule type",
#                     style={"width": "100%"}
#                 )
#             ], md=4),
#
#             dbc.Col([
#                 dbc.Label("Vessel Type:"),
#                 dcc.Dropdown(
#                     id="create-vessel-type",
#                     options=[{"label": "SF", "value": "SF"}, {"label": "BRX", "value": "BRX"}],
#                     value="SF",
#                     style={"width": "100%"}
#                 )
#             ], md=2),
#
#             dbc.Col([
#                 dbc.Label("Development Stage:"),
#                 dcc.Dropdown(
#                     id="create-dev-stage",
#                     options=[
#                         {"label": "MP", "value": "MP"},
#                         {"label": "pMP", "value": "pMP"},
#                         {"label": "BP", "value": "BP"},
#                         {"label": "BP SCC", "value": "BP SCC"},
#                         {"label": "MP SCC", "value": "MP SCC"},
#                     ],
#                     value="MP",
#                     style={"width": "100%"}
#                 )
#             ], md=2),
#
#             dbc.Col([
#                 dbc.Label("CLD Analyst:"),
#                 dcc.Dropdown(
#                     id="create-analyst",
#                     options=[
#                         {"label": "YY", "value": "YY"},
#                         {"label": "JS", "value": "JS"},
#                         {"label": "YW", "value": "YW"},
#                     ],
#                     placeholder="Select analyst",
#                     style={"width": "100%"}
#                 )
#             ], md=2),
#         ], className="mb-3"),
#
#         dbc.Row([
#             dbc.Col([
#                 dbc.Label("SIP #:"),
#                 dcc.Input(id="create-sip-number", type="number",
#                           placeholder="SIP#", style={"width": "100%"})
#             ], md=2),
#             dbc.Col([
#                 dbc.Label("UNIFI #:"),
#                 dcc.Input(id="create-unifi-number", type="number",
#                           placeholder="UNIFI#", style={"width": "100%"})
#             ], md=2),
#         ], className="mb-4"),
#
#         # Action buttons
#         dbc.Row([
#             dbc.Col(dbc.Button("➕ Add Row", id="add-sample-row", color="secondary", size="sm"), width="auto"),
#             dbc.Col(dbc.Button("🧹 Clear Table", id="clear-sample-table", color="danger", size="sm"), width="auto"),
#             dbc.Col(dbc.Button("💾 Save Samples", id="save-new-samples", color="primary", size="sm"), width="auto"),
#             dbc.Col(html.Div(id="create-samples-status", className="text-muted small"))
#         ], className="mb-3"),
#
#         # Sample creation table
#         dash_table.DataTable(
#             id="create-samples-table",
#             columns=[
#                 {"name": "Sample Number", "id": "sample_number", "editable": False},
#                 {"name": "Clone", "id": "cell_line", "editable": True},
#                 {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
#                 {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
#                 {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
#                 {"name": "ProAqa E Titer", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
#                 {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
#                 {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
#                 {"name": "Eluate Volume", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
#                 {"name": "Note", "id": "note", "editable": True}
#             ],
#             data=[],
#             editable=True,
#             row_deletable=True,
#             style_cell=TABLE_STYLE_CELL,
#             style_header=TABLE_STYLE_HEADER
#         )
#     ], style={"padding": "20px"})
#
#
# def sec_reports_view_layout():
#     """View existing SEC reports"""
#     return html.Div([
#         html.H3("📊 SEC Reports", className="text-primary mb-4"),
#         html.P("View and manage existing SEC analysis reports", className="text-muted"),
#
#         dbc.Card([
#             dbc.CardBody([
#                 html.P("SEC reports viewer will be implemented here", className="text-center text-muted")
#             ])
#         ])
#     ], style={"padding": "20px"})
#
#
# def sec_reports_create_layout():
#     """Create new SEC report - placeholder"""
#     return html.Div([
#         html.H3("➕ Create SEC Report", className="text-primary mb-4"),
#         html.P("Create a new SEC analysis report", className="text-muted"),
#
#         dbc.Alert([
#             html.H5("💡 Tip:", className="alert-heading"),
#             html.P(
#                 "To create SEC reports, navigate to Sample Set Analytics and click 'Create SEC Report' for the desired sample set.")
#         ], color="info")
#     ], style={"padding": "20px"})
#
#
# # ================== MAIN APP LAYOUT ==================
# app.layout = html.Div([
#     dcc.Location(id="url"),
#     dcc.Store(id="selected-sample-set", data={}),
#     get_sidebar(),
#     html.Div(id="page-content", style=CONTENT_STYLE)
# ])
#
#
# # ================== CALLBACKS ==================
# # Main page routing
# @app.callback(
#     Output("page-content", "children"),
#     Input("url", "pathname")
# )
# def display_page(pathname):
#     """Route pages based on URL pathname"""
#     if pathname == "/" or pathname == "/dashboard":
#         return dashboard_overview_layout()
#     elif pathname == "/fb-samples/view":
#         return fb_samples_view_layout()
#     elif pathname == "/analytics/sample-sets":
#         return sample_set_analytics_layout()
#     elif pathname == "/fb-samples/create":
#         return fb_samples_create_layout()
#     elif pathname == "/reports/sec/create":
#         return sec_reports_create_layout()
#     elif pathname == "/reports/sec/view":
#         return sec_reports_view_layout()
#     else:
#         return html.Div([
#             dbc.Alert([
#                 html.H4("404 - Page Not Found", className="alert-heading"),
#                 html.P("The page you're looking for doesn't exist."),
#                 html.Hr(),
#                 dbc.Button("Go to Dashboard", href="/", color="primary")
#             ], color="warning")
#         ], style={"padding": "50px"})
#
#
# # Load sample sets for analytics
# @app.callback(
#     Output("sample-sets-analytics-table", "data"),
#     Output("sample-sets-analytics-status", "children"),
#     [Input("refresh-sample-sets-btn", "n_clicks")],
#     prevent_initial_call=False
# )
# def load_sample_sets_analytics(n_clicks):
#     """Load sample sets for analytics"""
#     try:
#         data = get_sample_sets_with_analytics()
#         status = f"📊 Loaded {len(data)} sample sets ready for analytics"
#         return data, status
#     except Exception as e:
#         return [], f"❌ Error loading sample sets: {str(e)}"
#
#
# # Load all FB samples for viewing
# @app.callback(
#     Output("fb-samples-table", "data"),
#     Output("fb-samples-status", "children"),
#     [Input("refresh-samples-btn", "n_clicks"),
#      Input("save-samples-btn", "n_clicks")],
#     [State("fb-samples-table", "data")],
#     prevent_initial_call=False
# )
# def load_or_update_fb_samples(refresh_clicks, save_clicks, table_data):
#     """Load or update FB samples"""
#     ctx_triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
#
#     # If save button was clicked, update the database
#     if ctx_triggered == "save-samples-btn" and table_data:
#         updated = 0
#         errors = 0
#         for row in table_data:
#             try:
#                 update_data = {field: row.get(field) or None for field in EDITABLE_FIELDS}
#                 LimsUpstreamSamples.objects.filter(
#                     sample_number=row["sample_number"],
#                     sample_type=2
#                 ).update(**update_data)
#                 updated += 1
#             except Exception as e:
#                 print(f"Update failed for sample {row.get('sample_number')}: {e}")
#                 errors += 1
#
#     # Always reload data
#     samples = LimsUpstreamSamples.objects.filter(sample_type=2).order_by("-sample_number")
#     new_data = []
#
#     for s in samples:
#         # Calculate recoveries
#         fast_pro_a, a280 = calculate_recoveries(s)
#
#         # Build row data
#         row = {
#             "sample_number": s.sample_number,
#             "project": s.project or "",
#             "cell_line": s.cell_line or "",
#             "harvest_date": s.harvest_date.strftime("%Y-%m-%d") if s.harvest_date else None,
#             "development_stage": s.development_stage or "",
#             "sip_number": s.sip_number or "",
#             "analyst": s.analyst or "",
#             "hf_octet_titer": s.hf_octet_titer,
#             "pro_aqa_hf_titer": s.pro_aqa_hf_titer,
#             "pro_aqa_e_titer": s.pro_aqa_e_titer,
#             "proa_eluate_a280_conc": s.proa_eluate_a280_conc,
#             "hccf_loading_volume": s.hccf_loading_volume,
#             "proa_eluate_volume": s.proa_eluate_volume,
#             "fast_pro_a_recovery": fast_pro_a,
#             "purification_recovery_a280": a280,
#             "note": s.note or ""
#         }
#
#         # Check for SEC report
#         analysis = LimsSampleAnalysis.objects.filter(sample_id=f"FB{s.sample_number}").first()
#         if analysis and hasattr(analysis, 'sec_result') and analysis.sec_result and analysis.sec_result.report_id:
#             report_id = analysis.sec_result.report_id
#             row[
#                 "report_link"] = f'[🔗 SEC Report](/plotly_integration/dash-app/app/SecReportApp2/?report_id={report_id})'
#         else:
#             row["report_link"] = ""
#
#         new_data.append(row)
#
#     # Status message
#     if ctx_triggered == "save-samples-btn":
#         status = f"✅ Updated: {updated} samples | ❌ Errors: {errors}"
#     else:
#         status = f"📊 Loaded {len(new_data)} FB samples"
#
#     return new_data, status
#
#
# # Populate project dropdown for sample creation
# @app.callback(
#     Output("create-project-dropdown", "options"),
#     Input("url", "pathname"),
#     prevent_initial_call=False
# )
# def populate_project_dropdown(pathname):
#     """Populate project dropdown when on create samples page"""
#     if pathname != "/fb-samples/create":
#         raise dash.exceptions.PreventUpdate
#
#     project_qs = LimsProjectInformation.objects.all().order_by("protein", "molecule_type")
#
#     options = [
#         {
#             "label": f"{p.protein} - {p.molecule_type}",
#             "value": f"{p.protein}"
#         }
#         for p in project_qs if p.protein and p.molecule_type
#     ]
#
#     return options
#
#
# # Add/Clear rows for sample creation
# @app.callback(
#     Output("create-samples-table", "data"),
#     [Input("add-sample-row", "n_clicks"),
#      Input("clear-sample-table", "n_clicks")],
#     [State("create-samples-table", "data")],
#     prevent_initial_call=True
# )
# def modify_sample_creation_table(add_clicks, clear_clicks, current_data):
#     """Add or clear rows in sample creation table"""
#     if current_data is None:
#         current_data = []
#
#     ctx_triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
#
#     if ctx_triggered == "clear-sample-table":
#         return []
#
#     if ctx_triggered == "add-sample-row":
#         # Get next sample number
#         db_max = LimsUpstreamSamples.objects.filter(sample_type=2).aggregate(Max("sample_number"))
#         max_sample_number = db_max["sample_number__max"] or 0
#
#         # Check in-memory data
#         current_numbers = [
#             int(row["sample_number"]) for row in current_data
#             if str(row.get("sample_number")).isdigit()
#         ]
#         if current_numbers:
#             max_sample_number = max(max_sample_number, max(current_numbers))
#
#         next_sample_number = max_sample_number + 1
#
#         current_data.append({
#             "sample_number": next_sample_number,
#             "cell_line": "",
#             "harvest_date": "",
#             "hf_octet_titer": "",
#             "pro_aqa_hf_titer": "",
#             "pro_aqa_e_titer": "",
#             "proa_eluate_a280_conc": "",
#             "hccf_loading_volume": "",
#             "proa_eluate_volume": "",
#             "note": ""
#         })
#
#         return current_data
#
#     raise dash.exceptions.PreventUpdate
#
#
# # Save new samples
# @app.callback(
#     Output("create-samples-status", "children"),
#     Input("save-new-samples", "n_clicks"),
#     [State("create-samples-table", "data"),
#      State("create-project-dropdown", "value"),
#      State("create-vessel-type", "value"),
#      State("create-dev-stage", "value"),
#      State("create-analyst", "value"),
#      State("create-sip-number", "value"),
#      State("create-unifi-number", "value")],
#     prevent_initial_call=True
# )
# def save_new_samples(n_clicks, table_data, project, vessel_type, dev_stage, analyst, sip_number, unifi_number):
#     """Save new FB samples"""
#     if not table_data:
#         return "❌ No data to save."
#     if not project or not vessel_type:
#         return "⚠️ Please fill in Project and Vessel Type."
#
#     print(f"💾 Saving FB samples for project '{project}' | vessel: {vessel_type}")
#
#     created, skipped, errors = 0, 0, 0
#
#     for row in table_data:
#         try:
#             sample_number = row.get("sample_number")
#             if not sample_number:
#                 skipped += 1
#                 continue
#
#             _, created_flag = LimsUpstreamSamples.objects.update_or_create(
#                 sample_number=sample_number,
#                 sample_type=2,
#                 defaults={
#                     "project": project,
#                     "vessel_type": vessel_type,
#                     "sip_number": sip_number,
#                     "unifi_number": unifi_number,
#                     "development_stage": dev_stage,
#                     "analyst": analyst,
#                     "cell_line": row.get("cell_line") or "",
#                     "harvest_date": row.get("harvest_date") or None,
#                     "hf_octet_titer": row.get("hf_octet_titer") or None,
#                     "pro_aqa_hf_titer": row.get("pro_aqa_hf_titer") or None,
#                     "pro_aqa_e_titer": row.get("pro_aqa_e_titer") or None,
#                     "proa_eluate_a280_conc": row.get("proa_eluate_a280_conc") or None,
#                     "hccf_loading_volume": row.get("hccf_loading_volume") or None,
#                     "proa_eluate_volume": row.get("proa_eluate_volume") or None,
#                     "note": row.get("note") or "",
#                 }
#             )
#
#             # Also create LimsSampleAnalysis entry
#             LimsSampleAnalysis.objects.update_or_create(
#                 sample_id=f'FB{row["sample_number"]}',
#                 sample_type=2,
#                 defaults={
#                     "sample_date": row.get("harvest_date") or None,
#                     "project_id": project,
#                     "description": row.get("description", ""),
#                     "notes": row.get("note", ""),
#                     "dn": None,
#                     "a280_result": None
#                 }
#             )
#
#             created += 1 if created_flag else 0
#
#         except Exception as e:
#             print(f"❌ Error saving sample {row.get('sample_number')}: {e}")
#             errors += 1
#
#     return f"✅ Created/Updated: {created} | Skipped: {skipped} | Errors: {errors}"
from dash import html, dcc, dash_table, Input, Output, State, callback, ctx, ALL
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from plotly_integration.models import (
    LimsUpstreamSamples, Report, LimsSecResult, LimsSampleAnalysis,
    LimsProjectInformation, SampleMetadata, TimeSeriesData
)
from datetime import datetime, timedelta
from collections import defaultdict
import json
from django.db.models import Max, Q
import dash
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import re

# Create the Dash app
app = DjangoDash(
    "CLDDashboardApp2",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    title="CLD Analytics Dashboard"
)

# ================== TABLE CONFIGURATIONS ==================
TABLE_STYLE_CELL = {
    'textAlign': 'left',
    'fontSize': '11px',
    'fontFamily': 'Arial, sans-serif',
    'padding': '8px',
    'border': '1px solid #ddd'
}

TABLE_STYLE_HEADER = {
    'backgroundColor': '#f8f9fa',
    'fontWeight': 'bold',
    'fontSize': '11px',
    'textAlign': 'center',
    'border': '1px solid #ddd',
    'color': '#495057'
}

# Sample Set Analytics Columns
SAMPLE_SET_ANALYTICS_COLUMNS = [
    {"name": "Select", "id": "select", "type": "checkbox", "editable": True},
    {"name": "Project", "id": "project"},
    {"name": "Sample Range", "id": "range"},
    {"name": "SIP #", "id": "sip"},
    {"name": "Development Stage", "id": "development_stage"},
    {"name": "Sample Count", "id": "count"},
    {"name": "SEC Status", "id": "sec_status"},
    {"name": "Actions", "id": "actions", "presentation": "markdown"},
    {"name": "Preview", "id": "preview"}
]

# Sample Set Templates
SAMPLE_SET_TEMPLATES = {
    "By Project + SIP": {"group_by": ["project_id", "sip_number", "development_stage"]},
    "Weekly Batches": {"group_by": ["week", "project_id"]},
    "By Analyst": {"group_by": ["analyst", "project_id"]},
    "By Date Range": {"group_by": ["date_range", "project_id"]},
    "Custom": {"group_by": ["custom"]}
}

# Fields configuration
EDITABLE_FIELDS = ["cell_line", "harvest_date", "development_stage", "hf_octet_titer",
                   "hccf_loading_volume", "sip_number", "analyst", "pro_aqa_hf_titer",
                   "pro_aqa_e_titer", "proa_eluate_a280_conc", "proa_eluate_volume", "note"]

# ================== LAYOUT STYLES ==================
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "250px",
    "padding": "20px",
    "backgroundColor": "#f8f9fa",
    "borderRight": "1px solid #dee2e6",
    "overflowY": "auto",
    "zIndex": 1000
}

CONTENT_STYLE = {
    "marginLeft": "260px",
    "marginRight": "10px",
    "padding": "0px"
}


# ================== HELPER FUNCTIONS ==================
def calculate_recoveries(sample):
    """Calculate recovery percentages"""
    fast_pro_a_recovery = None
    a280_recovery = None

    try:
        if all([
            sample.proa_eluate_volume is not None,
            sample.pro_aqa_e_titer is not None,
            sample.hccf_loading_volume is not None,
            sample.pro_aqa_hf_titer is not None
        ]):
            fast_pro_a_recovery = (
                                          sample.proa_eluate_volume * sample.pro_aqa_e_titer
                                  ) / (
                                          sample.hccf_loading_volume * sample.pro_aqa_hf_titer
                                  ) * 100

        if all([
            sample.proa_eluate_volume is not None,
            sample.proa_eluate_a280_conc is not None,
            sample.hccf_loading_volume is not None,
            sample.pro_aqa_hf_titer is not None
        ]):
            a280_recovery = (
                                    sample.proa_eluate_volume * sample.proa_eluate_a280_conc
                            ) / (
                                    sample.hccf_loading_volume * sample.pro_aqa_hf_titer
                            ) * 100
    except ZeroDivisionError:
        pass

    return (
        round(fast_pro_a_recovery, 1) if fast_pro_a_recovery is not None else None,
        round(a280_recovery, 1) if a280_recovery is not None else None,
    )


def get_dashboard_stats():
    """Get statistics for dashboard cards"""
    try:
        # FB samples from LIMS
        total_fb_samples = LimsSampleAnalysis.objects.filter(sample_type=2).count()

        # Recent samples (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_samples = LimsSampleAnalysis.objects.filter(
            sample_type=2,
            created_at__gte=thirty_days_ago
        ).count()

        # SEC Reports count
        sec_reports = Report.objects.filter(analysis_type=1).count()

        # Pending analyses - samples without SEC results
        pending_analyses = LimsSampleAnalysis.objects.filter(
            sample_type=2,
            sec_result__isnull=True
        ).count()

        return {
            'total_samples': total_fb_samples,
            'recent_samples': recent_samples,
            'sec_reports': sec_reports,
            'pending_analyses': pending_analyses
        }
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {
            'total_samples': 0,
            'recent_samples': 0,
            'sec_reports': 0,
            'pending_analyses': 0
        }


def detect_sample_sets_by_pattern(samples):
    """Detect consecutive sample numbers as sets"""
    sample_sets = []

    # Group by project first
    project_groups = defaultdict(list)
    for sample in samples:
        # Extract sample number from sample_id (e.g., "FB1001" -> 1001)
        match = re.search(r'FB(\d+)', sample.sample_id)
        if match:
            sample_num = int(match.group(1))
            project_groups[sample.project_id].append((sample_num, sample))

    # Find consecutive ranges within each project
    for project, sample_list in project_groups.items():
        sample_list.sort(key=lambda x: x[0])  # Sort by sample number

        if not sample_list:
            continue

        ranges = []
        start = sample_list[0]
        end = sample_list[0]

        for i in range(1, len(sample_list)):
            if sample_list[i][0] - sample_list[i - 1][0] == 1:
                end = sample_list[i]
            else:
                ranges.append((start, end))
                start = sample_list[i]
                end = sample_list[i]
        ranges.append((start, end))

        # Create sample sets from ranges
        for start, end in ranges:
            sample_ids = [f"FB{num}" for num, _ in sample_list if start[0] <= num <= end[0]]
            sample_sets.append({
                "project": project,
                "range": f"FB{start[0]}-FB{end[0]}" if start[0] != end[0] else f"FB{start[0]}",
                "sample_ids": sample_ids,
                "count": len(sample_ids),
                "samples": [s for n, s in sample_list if start[0] <= n <= end[0]]
            })

    return sample_sets


def get_sample_sets_from_lims(grouping_template="By Project + SIP"):
    """Get sample sets from LimsSampleAnalysis with flexible grouping"""
    try:
        # Get FB samples from LIMS
        fb_samples = LimsSampleAnalysis.objects.filter(
            sample_type=2
        ).select_related('up', 'sec_result')

        if grouping_template == "Custom":
            # Use pattern detection for custom grouping
            return detect_sample_sets_by_pattern(fb_samples)

        # Standard grouping logic
        grouped = defaultdict(list)

        for sample in fb_samples:
            if grouping_template == "By Project + SIP":
                # Get upstream sample data if available
                up_sample = sample.up
                if up_sample:
                    key = (sample.project_id, up_sample.sip_number, up_sample.development_stage)
                else:
                    key = (sample.project_id, None, None)
            elif grouping_template == "Weekly Batches":
                week = sample.sample_date.isocalendar()[1] if sample.sample_date else 0
                year = sample.sample_date.year if sample.sample_date else 0
                key = (f"{year}-W{week:02d}", sample.project_id)
            elif grouping_template == "By Analyst":
                analyst = sample.up.analyst if sample.up else sample.analyst
                key = (analyst, sample.project_id)
            else:
                key = (sample.project_id,)

            grouped[key].append(sample)

        # Convert to table format
        table_data = []
        for key, samples in grouped.items():
            if not samples:
                continue

            sample_ids = [s.sample_id for s in samples]
            sample_nums = []
            for sid in sample_ids:
                match = re.search(r'FB(\d+)', sid)
                if match:
                    sample_nums.append(int(match.group(1)))

            if sample_nums:
                sample_nums.sort()
                sample_range = f"FB{sample_nums[0]}-FB{sample_nums[-1]}" if len(
                    sample_nums) > 1 else f"FB{sample_nums[0]}"
            else:
                sample_range = f"{len(samples)} samples"

            # Check SEC status
            samples_with_sec = sum(1 for s in samples if s.sec_result)
            if samples_with_sec == len(samples):
                sec_status = "✅ Complete"
            elif samples_with_sec > 0:
                sec_status = f"🟡 Partial ({samples_with_sec}/{len(samples)})"
            else:
                sec_status = "⚠️ Pending"

            # Build row data based on grouping type
            if grouping_template == "By Project + SIP":
                project, sip, dev_stage = key
                row = {
                    "project": project or "",
                    "sip": sip or "",
                    "development_stage": dev_stage or "",
                }
            elif grouping_template == "Weekly Batches":
                week, project = key
                row = {
                    "project": project or "",
                    "week": week,
                }
            elif grouping_template == "By Analyst":
                analyst, project = key
                row = {
                    "project": project or "",
                    "analyst": analyst or "",
                }
            else:
                row = {"project": key[0] or ""}

            row.update({
                "range": sample_range,
                "count": len(samples),
                "sec_status": sec_status,
                "sample_ids": sample_ids,
                "select": False
            })

            table_data.append(row)

        return table_data
    except Exception as e:
        print(f"Error getting sample sets from LIMS: {e}")
        return []


def generate_sec_preview(sample_ids):
    """Generate mini SEC chromatogram preview"""
    try:
        # Get first few samples for preview
        preview_samples = sample_ids[:3] if len(sample_ids) > 3 else sample_ids

        fig = go.Figure()

        for sample_id in preview_samples:
            # Try to get time series data
            result_id = None
            sample_metadata = SampleMetadata.objects.filter(
                sample_name=sample_id,
                analysis_type=1
            ).first()

            if sample_metadata:
                result_id = sample_metadata.result_id

            if result_id:
                time_series = TimeSeriesData.objects.filter(
                    result_id=result_id
                ).values('time', 'channel_1')[:500]  # Limit points for preview

                if time_series:
                    df = pd.DataFrame(time_series)
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df['channel_1'],
                        mode='lines',
                        name=sample_id,
                        line=dict(width=1)
                    ))

        fig.update_layout(
            height=150,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showticklabels=False, showgrid=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        return fig
    except Exception as e:
        print(f"Error generating preview: {e}")
        return go.Figure()


def create_stats_card(title, value, subtitle, color, icon):
    """Create a statistics card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H3(str(value), className="text-primary mb-0"),
                    html.P(title, className="text-muted mb-0"),
                    html.Small(subtitle, className="text-muted")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color}")
                ], className="align-self-center")
            ], className="d-flex")
        ])
    ], className="shadow-sm h-100")


# ================== LAYOUT COMPONENTS ==================
def get_sidebar():
    """Create the sidebar navigation"""
    return html.Div([
        html.H4("🧬 CLD Analytics", className="text-primary mb-3"),
        html.Hr(),

        dbc.Nav([
            # Dashboard
            dbc.NavLink([
                html.I(className="fas fa-tachometer-alt me-2"),
                "Dashboard"
            ], href="/", active="exact"),

            html.Hr(className="my-2"),

            # Sample Management
            html.P("SAMPLE MANAGEMENT", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className="fas fa-vial me-2"),
                "View All Samples"
            ], href="/fb-samples/view", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-layer-group me-2"),
                "Sample Set Analytics"
            ], href="/analytics/sample-sets", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-microscope me-2"),
                "SEC Viewer"
            ], href="/analytics/sec-viewer", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-plus me-2"),
                "Add Samples"
            ], href="/fb-samples/create", active="exact"),

            html.Hr(className="my-2"),

            # Analytics
            html.P("ANALYTICS", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className="fas fa-chart-bar me-2"),
                "Sample Comparison"
            ], href="/analytics/comparison", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-chart-line me-2"),
                "View SEC Reports"
            ], href="/reports/sec/view", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-plus-circle me-2"),
                "Create SEC Report"
            ], href="/reports/sec/create", active="exact"),

            html.Hr(className="my-2"),

            # Settings
            html.P("SYSTEM", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className="fas fa-download me-2"),
                "Export Analytics"
            ], href="/analytics/export", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-cogs me-2"),
                "Settings"
            ], href="/settings", active="exact")

        ], vertical=True, pills=True)
    ], style=SIDEBAR_STYLE)


def dashboard_overview_layout():
    """Main dashboard overview layout"""
    stats = get_dashboard_stats()

    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("🧬 CLD Analytics Dashboard", className="text-primary mb-1"),
                html.P("Cell Line Development - FB Sample Management & Analytics",
                       className="text-muted mb-4")
            ])
        ]),

        # Statistics Cards
        dbc.Row([
            dbc.Col([
                create_stats_card(
                    "Total FB Samples",
                    stats['total_samples'],
                    "All time",
                    "primary",
                    "fa-vial"
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "Recent Samples",
                    stats['recent_samples'],
                    "Last 30 days",
                    "success",
                    "fa-plus-circle"
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "SEC Reports",
                    stats['sec_reports'],
                    "Generated",
                    "info",
                    "fa-chart-line"
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "Pending Analyses",
                    stats['pending_analyses'],
                    "Awaiting analysis",
                    "warning",
                    "fa-clock"
                )
            ], md=3)
        ], className="mb-4"),

        # Quick Actions and Real-time Status
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("⚡ Quick Actions", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-chart-bar me-2"),
                                    "Sample Set Analytics"
                                ], color="primary", href="/analytics/sample-sets", size="lg",
                                    className="w-100 mb-2")
                            ], md=6),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-microscope me-2"),
                                    "Open SEC Viewer"
                                ], color="info", href="/analytics/sec-viewer",
                                    size="lg", className="w-100 mb-2")
                            ], md=6),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-rocket me-2"),
                                    "Batch Create Reports"
                                ], id="batch-create-btn", color="success",
                                    size="lg", className="w-100 mb-2")
                            ], md=6),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-download me-2"),
                                    "Export All Analytics"
                                ], id="export-all-btn", color="secondary",
                                    size="lg", className="w-100 mb-2")
                            ], md=6)
                        ])
                    ])
                ])
            ], md=8),

            # Real-time Activity with status updates
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📈 Live Status", className="mb-0"),
                        dcc.Interval(id='status-update-interval', interval=5000)  # 5 second updates
                    ]),
                    dbc.CardBody([
                        html.Div(id="live-status-feed", children=[
                            html.P("🟢 System operational", className="small mb-1"),
                            html.P("🔄 Checking for updates...", className="small mb-1"),
                        ])
                    ])
                ])
            ], md=4)
        ]),

        # Hidden components for batch operations
        dcc.Download(id="download-export-all"),
        html.Div(id="batch-create-status")
    ], style={"padding": "20px"})


def sample_set_analytics_layout():
    """Enhanced Sample Set Analytics layout"""
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3("📊 Sample Set Analytics", className="text-primary mb-1"),
                html.P("Advanced sample grouping and analysis", className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-sync me-1"),
                        "Refresh"
                    ], id="refresh-sample-sets-btn", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-magic me-1"),
                        "Auto-Detect Sets"
                    ], id="auto-detect-sets-btn", color="outline-info", size="sm")
                ])
            ], md=4, className="text-end")
        ], className="mb-3"),

        # Grouping Controls
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Grouping Template:", className="fw-bold"),
                        dcc.Dropdown(
                            id="grouping-template-dropdown",
                            options=[{"label": k, "value": k} for k in SAMPLE_SET_TEMPLATES.keys()],
                            value="By Project + SIP",
                            clearable=False
                        )
                    ], md=4),
                    dbc.Col([
                        html.Label("Quick Actions:", className="fw-bold"),
                        dbc.ButtonGroup([
                            dbc.Button("Create Reports for Selected",
                                       id="batch-create-selected-btn",
                                       color="success", size="sm"),
                            dbc.Button("Compare Selected",
                                       id="compare-selected-btn",
                                       color="info", size="sm")
                        ])
                    ], md=8)
                ])
            ])
        ], className="mb-4"),

        # Sample Sets Table with preview
        dash_table.DataTable(
            id="sample-sets-analytics-table",
            columns=SAMPLE_SET_ANALYTICS_COLUMNS,
            data=[],
            row_selectable="multi",
            filter_action="native",
            sort_action="native",
            page_action="native",
            page_size=25,
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER,
            style_data_conditional=[
                {
                    "if": {"filter_query": '{sec_status} contains "Complete"'},
                    "backgroundColor": "#d4edda",
                    "color": "#155724"
                },
                {
                    "if": {"filter_query": '{sec_status} contains "Partial"'},
                    "backgroundColor": "#fff3cd",
                    "color": "#856404"
                },
                {
                    "if": {"filter_query": '{sec_status} contains "Pending"'},
                    "backgroundColor": "#f8d7da",
                    "color": "#721c24"
                }
            ],
            markdown_options={"link_target": "_blank"}
        ),

        # Preview Modal
        dbc.Modal([
            dbc.ModalHeader("SEC Preview"),
            dbc.ModalBody([
                dcc.Graph(id="preview-graph", style={"height": "300px"})
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-preview-modal", className="ml-auto")
            ])
        ], id="preview-modal", size="lg"),

        # Status
        html.Div(id="sample-sets-analytics-status", className="text-muted small mt-2")
    ], style={"padding": "20px"})


def embedded_sec_viewer_layout():
    """Embedded SEC Report Viewer"""
    return html.Div([
        # Header with controls
        dbc.Row([
            dbc.Col([
                html.H3("🔬 SEC Analysis Viewer", className="text-primary mb-1"),
                html.P("Interactive SEC report viewer", className="text-muted")
            ], md=6),
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("Sample Set:"),
                    dcc.Dropdown(
                        id="sec-viewer-sample-set",
                        placeholder="Select a sample set to view",
                        style={"minWidth": "300px"}
                    ),
                    dbc.Button("Load", id="load-sec-viewer-btn", color="primary")
                ], size="sm")
            ], md=6, className="text-end")
        ], className="mb-3"),

        # Iframe container
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Iframe(
                        id="sec-viewer-iframe",
                        src="/plotly_integration/dash-app/app/SecReportApp2/?hide_report_tab=true",
                        style={
                            "width": "100%",
                            "height": "900px",
                            "border": "none",
                            "borderRadius": "5px"
                        }
                    )
                ], id="iframe-container")
            ])
        ], className="shadow-sm"),

        # Status
        html.Div(id="sec-viewer-status", className="text-muted small mt-2")
    ], style={"padding": "20px"})


def sample_comparison_layout():
    """Sample Set Comparison View"""
    return html.Div([
        html.H3("📊 Sample Set Comparison", className="text-primary mb-4"),

        # Selection controls
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Sample Sets to Compare (2-4):", className="fw-bold"),
                        dcc.Dropdown(
                            id="comparison-sample-sets",
                            multi=True,
                            placeholder="Select sample sets...",
                            maxHeight=300
                        )
                    ], md=8),
                    dbc.Col([
                        dbc.Button("Generate Comparison",
                                   id="generate-comparison-btn",
                                   color="primary",
                                   className="w-100")
                    ], md=4)
                ])
            ])
        ], className="mb-4"),

        # Comparison grid
        html.Div(id="comparison-grid", children=[
            dbc.Alert("Select sample sets to compare", color="info")
        ])
    ], style={"padding": "20px"})


def export_analytics_layout():
    """Export Analytics Layout"""
    return html.Div([
        html.H3("📥 Export Analytics", className="text-primary mb-4"),

        dbc.Card([
            dbc.CardBody([
                html.H5("Export Options", className="mb-3"),
                dbc.Checklist(
                    id="export-options",
                    options=[
                        {"label": "Sample Set Summary", "value": "summary"},
                        {"label": "SEC Results (HMW%, MP%, LMW%)", "value": "sec"},
                        {"label": "Titer Data", "value": "titer"},
                        {"label": "Recovery Calculations", "value": "recovery"},
                        {"label": "Complete Analytical Report", "value": "complete"}
                    ],
                    value=["summary", "sec"],
                    inline=False
                ),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Date Range:"),
                        dcc.DatePickerRange(
                            id="export-date-range",
                            start_date=(datetime.now() - timedelta(days=30)).date(),
                            end_date=datetime.now().date(),
                            display_format="YYYY-MM-DD"
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Format:"),
                        dcc.RadioItems(
                            id="export-format",
                            options=[
                                {"label": "Excel (.xlsx)", "value": "xlsx"},
                                {"label": "CSV (.csv)", "value": "csv"},
                                {"label": "PDF Report", "value": "pdf"}
                            ],
                            value="xlsx",
                            inline=True
                        )
                    ], md=6)
                ]),
                html.Hr(),
                dbc.Button("Generate Export",
                           id="generate-export-btn",
                           color="success",
                           size="lg",
                           className="w-100"),
                dcc.Download(id="download-export")
            ])
        ])
    ], style={"padding": "20px"})


# Keep existing layouts for other pages...
def fb_samples_view_layout():
    """FB samples view layout - existing code"""
    # [Keep the existing implementation]
    pass


def fb_samples_create_layout():
    """Create new FB samples layout - existing code"""
    # [Keep the existing implementation]
    pass


def sec_reports_view_layout():
    """View existing SEC reports - existing code"""
    # [Keep the existing implementation]
    pass


def sec_reports_create_layout():
    """Create new SEC report - existing code"""
    # [Keep the existing implementation]
    pass


# ================== MAIN APP LAYOUT ==================
app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="selected-sample-sets", data=[]),
    dcc.Store(id="sec-status-store", data={}),
    get_sidebar(),
    html.Div(id="page-content", style=CONTENT_STYLE)
])


# ================== CALLBACKS ==================
# Main page routing
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    """Route pages based on URL pathname"""
    if pathname == "/" or pathname == "/dashboard":
        return dashboard_overview_layout()
    elif pathname == "/fb-samples/view":
        return fb_samples_view_layout()
    elif pathname == "/analytics/sample-sets":
        return sample_set_analytics_layout()
    elif pathname == "/analytics/sec-viewer":
        return embedded_sec_viewer_layout()
    elif pathname == "/analytics/comparison":
        return sample_comparison_layout()
    elif pathname == "/analytics/export":
        return export_analytics_layout()
    elif pathname == "/fb-samples/create":
        return fb_samples_create_layout()
    elif pathname == "/reports/sec/create":
        return sec_reports_create_layout()
    elif pathname == "/reports/sec/view":
        return sec_reports_view_layout()
    else:
        return html.Div([
            dbc.Alert([
                html.H4("404 - Page Not Found", className="alert-heading"),
                html.P("The page you're looking for doesn't exist."),
                html.Hr(),
                dbc.Button("Go to Dashboard", href="/", color="primary")
            ], color="warning")
        ], style={"padding": "50px"})


# Enhanced sample sets loading with grouping templates
@app.callback(
    Output("sample-sets-analytics-table", "data"),
    Output("sample-sets-analytics-status", "children"),
    [Input("refresh-sample-sets-btn", "n_clicks"),
     Input("auto-detect-sets-btn", "n_clicks"),
     Input("grouping-template-dropdown", "value")],
    prevent_initial_call=False
)
def load_sample_sets_analytics(refresh_clicks, auto_clicks, grouping_template):
    """Load sample sets for analytics with flexible grouping"""
    try:
        ctx_triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        if ctx_triggered == "auto-detect-sets-btn":
            grouping_template = "Custom"

        data = get_sample_sets_from_lims(grouping_template)

        # Add action buttons and preview buttons
        for row in data:
            sample_ids = row.get("sample_ids", [])

            # Create action buttons
            actions = []
            if row["sec_status"] == "⚠️ Pending":
                actions.append(
                    f"[📊 Create SEC](/plotly_integration/dash-app/app/SecReportApp2/?samples={','.join(sample_ids)})")
            else:
                actions.append(
                    f"[👁️ View SEC](/plotly_integration/dash-app/app/SecReportApp2/?samples={','.join(sample_ids)})")

            row["actions"] = " | ".join(actions)
            row["preview"] = "🔍 Preview"

        status = f"📊 Loaded {len(data)} sample sets using '{grouping_template}' template"
        return data, status
    except Exception as e:
        return [], f"❌ Error loading sample sets: {str(e)}"


# SEC Viewer controls
@app.callback(
    Output("sec-viewer-sample-set", "options"),
    Input("url", "pathname"),
    prevent_initial_call=False
)
def populate_sec_viewer_dropdown(pathname):
    """Populate sample set dropdown for SEC viewer"""
    if pathname != "/analytics/sec-viewer":
        raise dash.exceptions.PreventUpdate

    try:
        sample_sets = get_sample_sets_from_lims()
        options = []

        for ss in sample_sets:
            label = f"{ss['project']} - {ss['range']} ({ss['count']} samples) {ss['sec_status']}"
            value = json.dumps({
                "sample_ids": ss["sample_ids"],
                "project": ss["project"]
            })
            options.append({"label": label, "value": value})

        return options
    except Exception as e:
        print(f"Error populating SEC viewer dropdown: {e}")
        return []


@app.callback(
    Output("sec-viewer-iframe", "src"),
    Output("sec-viewer-status", "children"),
    Input("load-sec-viewer-btn", "n_clicks"),
    State("sec-viewer-sample-set", "value"),
    prevent_initial_call=True
)
def update_sec_viewer(n_clicks, sample_set_json):
    """Update SEC viewer iframe with selected samples"""
    if not sample_set_json:
        return dash.no_update, "Please select a sample set"

    try:
        sample_set = json.loads(sample_set_json)
        sample_ids = sample_set["sample_ids"]

        # Build URL with sample parameters
        base_url = "/plotly_integration/dash-app/app/SecReportApp2/"
        params = f"?hide_report_tab=true&samples={','.join(sample_ids)}"

        return base_url + params, f"✅ Loaded {len(sample_ids)} samples"
    except Exception as e:
        return dash.no_update, f"❌ Error: {str(e)}"


# Batch operations
@app.callback(
    Output("batch-create-status", "children"),
    Input("batch-create-btn", "n_clicks"),
    Input("batch-create-selected-btn", "n_clicks"),
    State("sample-sets-analytics-table", "data"),
    State("sample-sets-analytics-table", "selected_rows"),
    prevent_initial_call=True
)
def batch_create_sec_reports(batch_all_clicks, batch_selected_clicks, table_data, selected_rows):
    """Create SEC reports for multiple sample sets"""
    ctx_triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    if ctx_triggered == "batch-create-btn":
        # Create for all pending sets
        pending_sets = [row for row in table_data if "Pending" in row.get("sec_status", "")]
    elif ctx_triggered == "batch-create-selected-btn" and selected_rows:
        # Create for selected sets
        pending_sets = [table_data[i] for i in selected_rows if i < len(table_data)]
    else:
        return dash.no_update

    created = 0
    for sample_set in pending_sets:
        try:
            sample_ids = sample_set.get("sample_ids", [])
            if sample_ids:
                # Create report (simplified - you'd implement actual report creation)
                report = Report.objects.create(
                    report_name=f"Auto-{sample_set['project']}-{sample_set['range']}",
                    project_id=sample_set['project'],
                    analysis_type=1,
                    sample_type="FB",
                    selected_samples=",".join(sample_ids),
                    user_id="batch_system",
                    date_created=datetime.now()
                )
                created += 1

                # Auto-link results if available
                for sample_id in sample_ids:
                    try:
                        sample = LimsSampleAnalysis.objects.get(sample_id=sample_id)
                        # Link SEC results if they exist
                        # [Implementation depends on your SEC result structure]
                    except:
                        pass
        except Exception as e:
            print(f"Error creating report for {sample_set.get('project')}: {e}")

    return dbc.Alert(f"✅ Created {created} SEC reports", color="success", dismissable=True)


# Live status updates
@app.callback(
    Output("live-status-feed", "children"),
    Input("status-update-interval", "n_intervals")
)
def update_live_status(n):
    """Update live status feed"""
    try:
        # Get current processing status
        pending = LimsSampleAnalysis.objects.filter(
            sample_type=2,
            sec_result__isnull=True
        ).count()

        # Get recent completions
        recent_complete = LimsSampleAnalysis.objects.filter(
            sample_type=2,
            sec_result__isnull=False,
            updated_at__gte=datetime.now() - timedelta(minutes=5)
        ).count()

        status_items = [
            html.P("🟢 System operational", className="small mb-1 text-success"),
            html.P(f"⏳ {pending} samples pending SEC analysis", className="small mb-1"),
        ]

        if recent_complete > 0:
            status_items.append(
                html.P(f"✅ {recent_complete} samples completed in last 5 min",
                       className="small mb-1 text-success")
            )

        status_items.append(
            html.P(f"🕐 Last update: {datetime.now().strftime('%H:%M:%S')}",
                   className="small mb-0 text-muted")
        )

        return status_items
    except Exception as e:
        return [html.P(f"❌ Error: {str(e)}", className="small text-danger")]


# Sample comparison
@app.callback(
    Output("comparison-sample-sets", "options"),
    Input("url", "pathname")
)
def populate_comparison_dropdown(pathname):
    """Populate comparison dropdown"""
    if pathname != "/analytics/comparison":
        raise dash.exceptions.PreventUpdate

    try:
        sample_sets = get_sample_sets_from_lims()
        return [
            {
                "label": f"{ss['project']} - {ss['range']} ({ss['count']} samples)",
                "value": json.dumps({"sample_ids": ss["sample_ids"], "name": ss["range"]})
            }
            for ss in sample_sets
        ]
    except:
        return []


@app.callback(
    Output("comparison-grid", "children"),
    Input("generate-comparison-btn", "n_clicks"),
    State("comparison-sample-sets", "value"),
    prevent_initial_call=True
)
def generate_comparison_view(n_clicks, selected_sets_json):
    """Generate comparison grid"""
    if not selected_sets_json or len(selected_sets_json) < 2:
        return dbc.Alert("Please select 2-4 sample sets to compare", color="warning")

    if len(selected_sets_json) > 4:
        return dbc.Alert("Maximum 4 sample sets can be compared at once", color="warning")

    try:
        # Create subplot grid
        cols = 2
        rows = (len(selected_sets_json) + 1) // 2

        plots = []
        for i, set_json in enumerate(selected_sets_json):
            sample_set = json.loads(set_json)

            # Generate mini plot for each set
            fig = generate_sec_preview(sample_set["sample_ids"][:5])  # Limit samples
            fig.update_layout(
                title=sample_set["name"],
                height=400
            )

            plots.append(
                dbc.Col([
                    dcc.Graph(figure=fig)
                ], md=6, className="mb-3")
            )

        return dbc.Row(plots)
    except Exception as e:
        return dbc.Alert(f"Error generating comparison: {str(e)}", color="danger")


# Export functionality
@app.callback(
    Output("download-export", "data"),
    Input("generate-export-btn", "n_clicks"),
    State("export-options", "value"),
    State("export-date-range", "start_date"),
    State("export-date-range", "end_date"),
    State("export-format", "value"),
    prevent_initial_call=True
)
def generate_export(n_clicks, options, start_date, end_date, format):
    """Generate comprehensive export"""
    try:
        # Build export data
        export_data = {}

        if "summary" in options or "complete" in options:
            sample_sets = get_sample_sets_from_lims()
            export_data["sample_sets"] = pd.DataFrame(sample_sets)

        if "sec" in options or "complete" in options:
            # Get SEC results
            sec_results = []
            analyses = LimsSampleAnalysis.objects.filter(
                sample_type=2,
                sec_result__isnull=False,
                sample_date__range=[start_date, end_date]
            ).select_related('sec_result')

            for analysis in analyses:
                if analysis.sec_result:
                    sec_results.append({
                        "sample_id": analysis.sample_id,
                        "project": analysis.project_id,
                        "hmw": analysis.sec_result.hmw,
                        "main_peak": analysis.sec_result.main_peak,
                        "lmw": analysis.sec_result.lmw,
                        "status": analysis.sec_result.status,
                        "date": analysis.sample_date
                    })

            export_data["sec_results"] = pd.DataFrame(sec_results)

        if "titer" in options or "complete" in options:
            # Get titer data from upstream samples
            titer_data = []
            up_samples = LimsUpstreamSamples.objects.filter(
                sample_type=2,
                harvest_date__range=[start_date, end_date]
            )

            for sample in up_samples:
                titer_data.append({
                    "sample_id": f"FB{sample.sample_number}",
                    "hf_octet_titer": sample.hf_octet_titer,
                    "pro_aqa_hf_titer": sample.pro_aqa_hf_titer,
                    "pro_aqa_e_titer": sample.pro_aqa_e_titer,
                })

            export_data["titer_data"] = pd.DataFrame(titer_data)

        if "recovery" in options or "complete" in options:
            # Calculate recoveries
            recovery_data = []
            for sample in up_samples:
                fast_pro_a, a280 = calculate_recoveries(sample)
                recovery_data.append({
                    "sample_id": f"FB{sample.sample_number}",
                    "fast_pro_a_recovery": fast_pro_a,
                    "a280_recovery": a280
                })

            export_data["recovery_data"] = pd.DataFrame(recovery_data)

        # Generate file
        if format == "xlsx":
            # Create Excel with multiple sheets
            from io import BytesIO
            output = BytesIO()

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for sheet_name, df in export_data.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

            output.seek(0)
            filename = f"CLD_Analytics_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            return dcc.send_bytes(output.read(), filename)

        elif format == "csv":
            # For CSV, just export the first dataset
            if export_data:
                df = list(export_data.values())[0]
                filename = f"CLD_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                return dcc.send_data_frame(df.to_csv, filename, index=False)

        # PDF would require additional libraries like reportlab

    except Exception as e:
        print(f"Export error: {e}")
        return dash.no_update


# Preview modal handling
@app.callback(
    Output("preview-modal", "is_open"),
    Output("preview-graph", "figure"),
    [Input({"type": "preview-btn", "index": ALL}, "n_clicks"),
     Input("close-preview-modal", "n_clicks")],
    State("sample-sets-analytics-table", "data"),
    prevent_initial_call=True
)
def toggle_preview_modal(preview_clicks, close_click, table_data):
    """Handle preview modal"""
    ctx_triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else None

    if "close-preview-modal" in ctx_triggered:
        return False, go.Figure()

    # Find which preview button was clicked
    # [Implementation depends on how you structure the preview buttons]

    return True, generate_sec_preview(["FB1001", "FB1002", "FB1003"])  # Example

# Keep existing callbacks for other functionality...
# [Include all the existing callbacks from the original file]