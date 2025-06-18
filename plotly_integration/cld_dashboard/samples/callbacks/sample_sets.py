# # Sample sets callbacks for CLD Dashboard - Connected to real data
#
# from dash import Input, Output, State, callback, html, no_update
# import dash_bootstrap_components as dbc
# import pandas as pd
# from django.db.models import Count, Q
# from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, Report, LimsProjectInformation
# from ...config.analysis_types import ANALYSIS_TYPES, STATUS_COLORS
# from ...shared.styles.common_styles import COLORS
# import json
# from datetime import datetime, timedelta
#
#
# @callback(
#     [Output("sample-sets-grid", "children"),
#      Output("sample-sets-loading-output", "children")],
#     [Input("apply-filters-btn", "n_clicks"),
#      Input("refresh-sample-sets-btn", "n_clicks"),
#      Input("parsed-pathname", "data")],
#     [State("project-filter", "value"),
#      State("status-filter", "value"),
#      State("search-sample-sets", "value")]
# )
# def update_sample_sets_grid(apply_clicks, refresh_clicks, pathname, project_filter, status_filter, search_term):
#     """Update the sample sets grid based on filters"""
#     if pathname != "/sample-sets":
#         return no_update, no_update
#
#     try:
#         # Get sample sets data from CLD database
#         sample_sets_data = get_sample_sets_data_from_db(project_filter, status_filter, search_term)
#
#         if not sample_sets_data:
#             return dbc.Alert([
#                 html.I(className="fas fa-info-circle me-2"),
#                 "No sample sets found. Check your filters or create some samples first."
#             ], color="info"), ""
#
#         # Create grid cards
#         grid_cards = []
#         for i in range(0, len(sample_sets_data), 3):  # 3 cards per row
#             row_cards = sample_sets_data[i:i + 3]
#             grid_cards.append(
#                 dbc.Row([
#                     dbc.Col([
#                         create_sample_set_card(card_data)
#                     ], md=4) for card_data in row_cards
#                 ], className="mb-3")
#             )
#
#         return html.Div(grid_cards), ""
#
#     except Exception as e:
#         error_msg = f"Error loading sample sets: {str(e)}"
#         return dbc.Alert([
#             html.I(className="fas fa-exclamation-triangle me-2"),
#             error_msg
#         ], color="danger"), ""
#
#
# @callback(
#     Output("sample-sets-table", "data"),
#     [Input("apply-filters-btn", "n_clicks"),
#      Input("refresh-sample-sets-btn", "n_clicks"),
#      Input("parsed-pathname", "data")],
#     [State("project-filter", "value"),
#      State("status-filter", "value"),
#      State("search-sample-sets", "value")]
# )
# def update_sample_sets_table(apply_clicks, refresh_clicks, pathname, project_filter, status_filter, search_term):
#     """Update the sample sets table data"""
#     if pathname != "/sample-sets/table":
#         return no_update
#
#     try:
#         sample_sets_data = get_sample_sets_data_from_db(project_filter, status_filter, search_term)
#
#         # Format data for table
#         table_data = []
#         for set_data in sample_sets_data:
#             table_data.append({
#                 "set_name": set_data["set_name"],
#                 "project": set_data["project"],
#                 "sip_number": set_data["sip_number"] or "",
#                 "development_stage": set_data["development_stage"] or "",
#                 "sample_count": set_data["sample_count"],
#                 "sec_status": create_status_badge_markdown(set_data["sec_status"]),
#                 "actions": create_action_buttons_markdown(set_data)
#             })
#
#         return table_data
#
#     except Exception as e:
#         return []
#
#
# @callback(
#     [Output("sample-set-info", "children"),
#      Output("analysis-status-info", "children"),
#      Output("samples-in-set-table", "children"),
#      Output("sample-count-badge", "children")],
#     [Input("url", "search")],
#     [State("parsed-pathname", "data")]
# )
# def update_sample_set_detail(search, pathname):
#     """Update sample set detail page"""
#     if pathname != "/sample-sets/view":
#         return no_update, no_update, no_update, no_update
#
#     # Parse query parameters
#     from urllib.parse import parse_qs
#     query_params = parse_qs(search.lstrip('?')) if search else {}
#
#     project = query_params.get('project', [''])[0]
#     sip = query_params.get('sip', [''])[0]
#     stage = query_params.get('stage', [''])[0]
#
#     if not project:
#         return "No project specified", "", "", "0"
#
#     try:
#         # Get samples in this set from CLD database
#         filters = Q(project=project)
#         if sip:
#             filters &= Q(sip_number=sip)
#         if stage:
#             filters &= Q(development_stage=stage)
#
#         # Query LimsUpstreamSamples
#         samples = LimsUpstreamSamples.objects.filter(filters).order_by('sample_number')
#
#         if not samples:
#             return "No samples found", "", "", "0"
#
#         # Sample set information
#         sample_info = html.Div([
#             html.P([html.Strong("🧬 Project: "), project]),
#             html.P([html.Strong("📋 SIP Number: "), sip or "N/A"]),
#             html.P([html.Strong("🔬 Development Stage: "), stage or "N/A"]),
#             html.P([html.Strong("🧪 Total Samples: "), str(len(samples))]),
#             html.P([html.Strong("📅 Date Range: "), get_sample_date_range_from_db(samples)])
#         ])
#
#         # Analysis status - check for SEC results
#         sec_reports = Report.objects.filter(
#             analysis_type=1,  # SEC
#             project_id=project
#         ).count()
#
#         # Also check LimsSampleAnalysis for SEC results
#         sample_ids = [f"FB{s.sample_number}" for s in samples]
#         sec_analysis_count = LimsSampleAnalysis.objects.filter(
#             sample_id__in=sample_ids,
#             sec_result__isnull=False
#         ).count()
#
#         analysis_status = html.Div([
#             create_analysis_status_item("🧪 SEC Analysis", sec_reports > 0 or sec_analysis_count > 0),
#             create_analysis_status_item("🔬 Titer Analysis", False),
#             create_analysis_status_item("📊 AKTA Analysis", False)
#         ])
#
#         # Samples table
#         samples_table = create_samples_in_set_table_from_db(samples)
#
#         return sample_info, analysis_status, samples_table, str(len(samples))
#
#     except Exception as e:
#         error_msg = f"Error loading sample set: {str(e)}"
#         return error_msg, "", "", "0"
#
#
# def get_sample_sets_data_from_db(project_filter=None, status_filter=None, search_term=None):
#     """Get sample sets data from CLD database"""
#     try:
#         # Get all UP samples (sample_type=2) and group them
#         samples = LimsUpstreamSamples.objects.filter(sample_type=2)
#
#         if project_filter and project_filter != "all":
#             samples = samples.filter(project=project_filter)
#
#         if search_term:
#             samples = samples.filter(
#                 Q(project__icontains=search_term) |
#                 Q(sip_number__icontains=search_term) |
#                 Q(development_stage__icontains=search_term) |
#                 Q(cell_line__icontains=search_term)
#             )
#
#         # Group by project, sip_number, development_stage
#         grouped_data = {}
#         for sample in samples:
#             key = (sample.project, sample.sip_number, sample.development_stage)
#             if key not in grouped_data:
#                 grouped_data[key] = []
#             grouped_data[key].append(sample)
#
#         # Convert to sample sets format
#         sample_sets = []
#         for (project, sip, stage), samples_list in grouped_data.items():
#             # Check SEC analysis status
#             sample_ids = [f"FB{s.sample_number}" for s in samples_list]
#
#             # Check for SEC reports
#             sec_reports = Report.objects.filter(
#                 analysis_type=1,
#                 project_id=project
#             ).count()
#
#             # Check for SEC results in LIMS
#             sec_analysis = LimsSampleAnalysis.objects.filter(
#                 sample_id__in=sample_ids,
#                 sec_result__isnull=False
#             ).count()
#
#             if sec_reports > 0 or sec_analysis > 0:
#                 sec_status = "Completed"
#             elif LimsSampleAnalysis.objects.filter(sample_id__in=sample_ids).exists():
#                 sec_status = "Data Available"
#             else:
#                 sec_status = "No Analysis"
#
#             set_name = f"{project}"
#             if sip:
#                 set_name += f"_SIP{sip}"
#             if stage:
#                 set_name += f"_{stage}"
#
#             sample_sets.append({
#                 "set_name": set_name,
#                 "project": project,
#                 "sip_number": sip,
#                 "development_stage": stage,
#                 "sample_count": len(samples_list),
#                 "sec_status": sec_status,
#                 "sample_ids": sample_ids,
#                 "last_updated": max([s.created_at for s in samples_list if s.created_at], default=datetime.now())
#             })
#
#         # Apply status filter
#         if status_filter and status_filter != "all":
#             if status_filter == "none":
#                 sample_sets = [s for s in sample_sets if s["sec_status"] == "No Analysis"]
#             elif status_filter == "completed":
#                 sample_sets = [s for s in sample_sets if s["sec_status"] == "Completed"]
#             elif status_filter == "available":
#                 sample_sets = [s for s in sample_sets if s["sec_status"] == "Data Available"]
#
#         return sorted(sample_sets, key=lambda x: x["last_updated"], reverse=True)
#
#     except Exception as e:
#         print(f"Error getting sample sets data: {e}")
#         return []
#
#
# def create_sample_set_card(set_data):
#     """Create a card for displaying sample set information"""
#     set_name = set_data.get('set_name', 'Unknown Set')
#     project = set_data.get('project', '')
#     sip = set_data.get('sip_number', '')
#     stage = set_data.get('development_stage', '')
#     sample_count = set_data.get('sample_count', 0)
#     sec_status = set_data.get('sec_status', 'No Analysis')
#
#     # Determine status color and icon
#     status_color = "secondary"
#     status_icon = "fa-question"
#
#     if sec_status == "Completed":
#         status_color = "success"
#         status_icon = "fa-check-circle"
#     elif sec_status == "In Progress":
#         status_color = "warning"
#         status_icon = "fa-clock"
#     elif sec_status == "Data Available":
#         status_color = "info"
#         status_icon = "fa-database"
#
#     return dbc.Card([
#         dbc.CardHeader([
#             html.Div([
#                 html.H6([
#                     html.I(className="fas fa-layer-group me-2 text-primary"),
#                     set_name
#                 ], className="mb-0"),
#                 dbc.Badge([
#                     html.I(className=f"fas {status_icon} me-1"),
#                     sec_status
#                 ], color=status_color, className="float-end")
#             ])
#         ]),
#         dbc.CardBody([
#             html.P([
#                 html.I(className="fas fa-project-diagram text-primary me-2"),
#                 html.Strong("Project: "), project, html.Br(),
#                 html.I(className="fas fa-hashtag text-info me-2"),
#                 html.Strong("SIP: "), sip or "N/A", html.Br(),
#                 html.I(className="fas fa-flask text-success me-2"),
#                 html.Strong("Stage: "), stage or "N/A", html.Br(),
#                 html.I(className="fas fa-vial text-warning me-2"),
#                 html.Strong("Samples: "), f"{sample_count} samples"
#             ], className="small"),
#
#             dbc.ButtonGroup([
#                 dbc.Button([
#                     html.I(className="fas fa-eye me-1"),
#                     "View"
#                 ],
#                     href=f"#!/sample-sets/view?project={project}&sip={sip}&stage={stage}",
#                     color="outline-primary",
#                     size="sm"),
#                 dbc.Button([
#                     html.I(className="fas fa-microscope me-1"),
#                     "SEC"
#                 ],
#                     id={"type": "request-sec-btn", "index": set_name},
#                     color="primary" if sec_status == "No Analysis" else "outline-success",
#                     size="sm",
#                     disabled=(sec_status == "Completed"))
#             ], size="sm")
#         ])
#     ], className="mb-3 shadow-sm")
#
#
# def create_status_badge_markdown(status):
#     """Create markdown for status badge in table"""
#     color_map = {
#         "No Analysis": "secondary",
#         "Requested": "warning",
#         "In Progress": "info",
#         "Data Available": "info",
#         "Completed": "success"
#     }
#     color = color_map.get(status, "secondary")
#     return f'<span class="badge bg-{color}">{status}</span>'
#
#
# def create_action_buttons_markdown(set_data):
#     """Create markdown for action buttons in table"""
#     project = set_data.get('project', '')
#     sip = set_data.get('sip_number', '')
#     stage = set_data.get('development_stage', '')
#
#     view_url = f"#!/sample-sets/view?project={project}&sip={sip}&stage={stage}"
#     return f'[👁️ View]({view_url}) [🔬 SEC](#!/analysis/sec)'
#
#
# def create_analysis_status_item(analysis_name, has_data):
#     """Create analysis status display item"""
#     if has_data:
#         icon = "fa-check-circle"
#         color = "success"
#         status = "Available"
#     else:
#         icon = "fa-clock"
#         color = "warning"
#         status = "Pending"
#
#     return html.Div([
#         html.I(className=f"fas {icon} text-{color} me-2"),
#         html.Strong(analysis_name),
#         f": {status}"
#     ], className="mb-2")
#
#
# def create_samples_in_set_table_from_db(samples):
#     """Create table showing samples in the set from CLD database"""
#     from dash import dash_table
#
#     table_data = []
#     for sample in samples:
#         # Check if SEC data exists
#         sample_id = f"FB{sample.sample_number}"
#         try:
#             analysis = LimsSampleAnalysis.objects.filter(sample_id=sample_id).first()
#             has_sec = analysis and hasattr(analysis, 'sec_result') and analysis.sec_result
#         except:
#             has_sec = False
#
#         table_data.append({
#             "sample_id": sample_id,
#             "sample_number": sample.sample_number,
#             "cell_line": sample.cell_line or "",
#             "harvest_date": sample.harvest_date.strftime("%Y-%m-%d") if sample.harvest_date else "",
#             "analyst": sample.analyst or "",
#             "sec_data": "✅" if has_sec else "❌"
#         })
#
#     return dash_table.DataTable(
#         columns=[
#             {"name": "Sample ID", "id": "sample_id", "type": "text"},
#             {"name": "Sample #", "id": "sample_number", "type": "numeric"},
#             {"name": "Cell Line", "id": "cell_line", "type": "text"},
#             {"name": "Harvest Date", "id": "harvest_date", "type": "text"},
#             {"name": "Analyst", "id": "analyst", "type": "text"},
#             {"name": "SEC Data", "id": "sec_data", "type": "text"}
#         ],
#         data=table_data,
#         sort_action="native",
#         page_action="native",
#         page_size=10,
#         style_cell={'textAlign': 'left', 'fontSize': '12px'},
#         style_header={'backgroundColor': '#1976d2', 'fontWeight': 'bold', 'color': 'white'},
#         style_data_conditional=[
#             {
#                 'if': {'filter_query': '{sec_data} = ✅'},
#                 'backgroundColor': '#e8f5e8',
#                 'color': 'green'
#             },
#             {
#                 'if': {'filter_query': '{sec_data} = ❌'},
#                 'backgroundColor': '#ffeaea',
#                 'color': 'red'
#             }
#         ]
#     )
#
#
# def get_sample_date_range_from_db(samples):
#     """Get date range for samples from CLD database"""
#     dates = [s.harvest_date for s in samples if s.harvest_date]
#     if not dates:
#         dates = [s.created_at for s in samples if s.created_at]
#
#     if not dates:
#         return "N/A"
#
#     min_date = min(dates).strftime("%Y-%m-%d")
#     max_date = max(dates).strftime("%Y-%m-%d")
#
#     if min_date == max_date:
#         return min_date
#     else:
#         return f"{min_date} to {max_date}"
#
#
# @callback(
#     [Output("project-filter", "options"),
#      Output("project-filter", "value")],
#     [Input("parsed-pathname", "data")]
# )
# def populate_project_filter(pathname):
#     """Populate project filter dropdown from CLD database"""
#     if pathname != "/sample-sets":
#         return [], "all"
#
#     try:
#         # Get unique projects from CLD database
#         projects = LimsUpstreamSamples.objects.values_list('project', flat=True).distinct()
#         projects = [p for p in projects if p]  # Remove None values
#
#         options = [{"label": "All Projects", "value": "all"}]
#         for project in sorted(projects):
#             options.append({"label": f"🧬 {project}", "value": project})
#
#         return options, "all"
#     except Exception as e:
#         print(f"Error loading projects: {e}")
#         return [{"label": "All Projects", "value": "all"}], "all"