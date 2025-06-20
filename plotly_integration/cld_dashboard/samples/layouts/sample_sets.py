# # cld_dashboard/samples/layouts/sample_sets.py
#
# import dash
# from dash import html, dcc, dash_table
# import dash_bootstrap_components as dbc
#
# # Make sure this import path is correct for your project structure
# try:
#     from ...shared.styles.common_styles import CARD_STYLE, COLORS
# except ImportError:
#     # Fallback if import fails
#     CARD_STYLE = {}
#     COLORS = {}
#     print("Warning: Could not import common_styles")
#
#
# def create_sample_sets_layout():
#     """Create the sample sets management page"""
#     return dbc.Container([
#         # Header
#         dbc.Row([
#             dbc.Col([
#                 html.H2([
#                     html.I(className="fas fa-layer-group text-primary me-2"),
#                     "Sample Sets Analysis Management"
#                 ]),
#                 html.P("Manage analysis requests and track progress for grouped samples",
#                        className="text-muted")
#             ], md=8),
#             dbc.Col([
#                 dbc.ButtonGroup([
#                     dbc.Button([
#                         html.I(className="fas fa-sync-alt me-1"),
#                         "Refresh"
#                     ], id="refresh-sample-sets-btn", color="outline-primary", size="sm"),
#                     dbc.Button([
#                         html.I(className="fas fa-file-export me-1"),
#                         "Export"
#                     ], id="export-sample-sets-btn", color="outline-info", size="sm")
#                 ], className="float-end")
#             ], md=4)
#         ], className="mb-4"),
#
#         # Metrics Row
#         dbc.Row([
#             dbc.Col([
#                 create_metric_card("Total Sets", "0", "fa-layer-group", "primary", "total-sets-metric")
#             ], md=3),
#             dbc.Col([
#                 create_metric_card("Pending Analysis", "0", "fa-clock", "warning", "pending-metric")
#             ], md=3),
#             dbc.Col([
#                 create_metric_card("In Progress", "0", "fa-spinner", "info", "in-progress-metric")
#             ], md=3),
#             dbc.Col([
#                 create_metric_card("Completed", "0", "fa-check-circle", "success", "completed-metric")
#             ], md=3)
#         ], className="mb-4"),
#
#         # Filter Row
#         dbc.Row([
#             dbc.Col([
#                 dbc.Card([
#                     dbc.CardBody([
#                         dbc.Row([
#                             dbc.Col([
#                                 html.Label("Search", className="fw-bold small"),
#                                 dbc.Input(
#                                     id="search-sample-sets",
#                                     placeholder="Search by project, SIP, or stage...",
#                                     type="text"
#                                 )
#                             ], md=4),
#                             dbc.Col([
#                                 html.Label("Project Filter", className="fw-bold small"),
#                                 dcc.Dropdown(
#                                     id="project-filter",
#                                     options=[{"label": "All Projects", "value": "all"}],
#                                     value="all",
#                                     clearable=False
#                                 )
#                             ], md=4),
#                             dbc.Col([
#                                 html.Label("Status Filter", className="fw-bold small"),
#                                 dcc.Dropdown(
#                                     id="status-filter",
#                                     options=[
#                                         {"label": "All Status", "value": "all"},
#                                         {"label": "Has Pending", "value": "pending"},
#                                         {"label": "All Complete", "value": "complete"},
#                                         {"label": "No Analysis", "value": "none"}
#                                     ],
#                                     value="all",
#                                     clearable=False
#                                 )
#                             ], md=4)
#                         ])
#                     ])
#                 ], className="shadow-sm")
#             ])
#         ], className="mb-4"),
#
#         # Sample Sets Grid
#         dbc.Row([
#             dbc.Col([
#                 html.Div(id="sample-sets-grid", children=[
#                     dbc.Spinner(
#                         html.Div(style={"height": "200px"}),
#                         color="primary"
#                     )
#                 ])
#             ])
#         ]),
#
#         # Analysis Request Modal
#         create_analysis_request_modal(),
#
#         # Sample Set Details Modal
#         create_sample_set_details_modal(),
#
#         # Toast notifications
#         html.Div(id="sample-sets-notifications"),
#
#         # Hidden stores
#         dcc.Store(id="selected-sample-set", data={}),
#         dcc.Store(id="available-projects", data=[]),
#
#         # Dummy output for callbacks that don't need real output
#         html.Div(id="dummy-output", style={"display": "none"})
#
#     ], fluid=True, style={"padding": "20px"})
#
#
# def create_metric_card(title, metric_id, icon, color, card_id):
#     """Create a metric display card"""
#     return dbc.Card([
#         dbc.CardBody([
#             html.Div([
#                 html.Div([
#                     html.H3("0", id=card_id, className=f"text-{color} mb-0"),
#                     html.P(title, className="text-muted mb-0 small")
#                 ], className="flex-grow-1"),
#                 html.Div([
#                     html.I(className=f"fas {icon} fa-2x text-{color} opacity-75")
#                 ], className="align-self-center")
#             ], className="d-flex")
#         ])
#     ], className="shadow-sm h-100")
#
#
# def create_sample_set_card(sample_set, analysis_status):
#     """Create a card for a single sample set - now full width with properly configured SEC button"""
#     # Determine overall status
#     has_pending = any(status == 'requested' for status in analysis_status.values())
#     has_in_progress = any(status == 'in_progress' for status in analysis_status.values())
#     all_complete = all(status == 'completed' for status in analysis_status.values()
#                        if status != 'not_requested')
#
#     if has_pending:
#         overall_status = {"color": "warning", "icon": "fa-clock", "text": "Pending"}
#     elif has_in_progress:
#         overall_status = {"color": "info", "icon": "fa-spinner", "text": "In Progress"}
#     elif all_complete and any(status == 'completed' for status in analysis_status.values()):
#         overall_status = {"color": "success", "icon": "fa-check-circle", "text": "Completed"}
#     else:
#         overall_status = {"color": "secondary", "icon": "fa-circle", "text": "No Analysis"}
#
#     # Get sample IDs for this set
#     sample_ids = [member.sample.sample_id for member in sample_set.members.all()]
#
#     # Check for existing SEC reports to determine button configuration
#     from plotly_integration.models import Report
#     sec_reports = Report.objects.filter(
#         analysis_type=1,  # SEC
#         project_id=sample_set.project_id
#     ).order_by('-date_created')
#
#     # Determine SEC button href and appearance
#     if sec_reports.exists():
#         latest_report = sec_reports.first()
#         sec_href = f"/plotly_integration/dash-app/app/SecReportApp2/?report_id={latest_report.report_id}"
#         sec_button_text = "View SEC Report"
#     else:
#         sec_href = "/plotly_integration/dash-app/app/SecReportApp2/"
#         sec_button_text = "Open SEC App"
#
#     return dbc.Card([
#         dbc.CardBody([
#             dbc.Row([
#                 # Left section: Basic info
#                 dbc.Col([
#                     html.Div([
#                         html.H5(sample_set.set_name, className="mb-1"),
#                         html.P([
#                             html.I(className="fas fa-vial text-primary me-2"),
#                             f"{sample_set.sample_count} samples",
#                             html.Span(" | ", className="text-muted"),
#                             html.I(className="fas fa-calendar text-info me-2"),
#                             f"Created: {sample_set.created_at.strftime('%Y-%m-%d')}" if sample_set.created_at else "Unknown"
#                         ], className="mb-2 text-muted small"),
#                     ])
#                 ], md=3),
#
#                 # Middle section: Analysis badges
#                 dbc.Col([
#                     html.Div([
#                         html.P("Analysis Status:", className="fw-bold small mb-2"),
#                         html.Div([
#                             create_analysis_badge(analysis_type, status)
#                             for analysis_type, status in analysis_status.items()
#                         ], className="d-flex flex-wrap gap-1")
#                     ])
#                 ], md=6),
#
#                 # Right section: Actions and overall status
#                 dbc.Col([
#                     html.Div([
#                         dbc.Badge([
#                             html.I(className=f"fas {overall_status['icon']} me-1"),
#                             overall_status['text']
#                         ], color=overall_status['color'], className="mb-2"),
#
#                         dbc.ButtonGroup([
#                             dbc.Button([
#                                 html.I(className="fas fa-microscope me-1"),
#                                 "Request Analysis"
#                             ],
#                                 id={"type": "request-analysis-btn", "index": sample_set.id},
#                                 color="primary",
#                                 size="sm"),
#
#                             # SEC button configured as a link
#                             html.A(
#                                 dbc.Button([
#                                     html.I(className="fas fa-chart-line me-1"),
#                                     sec_button_text
#                                 ],
#                                     color="success" if analysis_status.get('SEC') == 'completed' else "outline-success",
#                                     size="sm",
#                                     disabled=False  # Always enabled now
#                                 ),
#                                 href=sec_href,
#                                 target="_blank",
#                                 style={"textDecoration": "none"}
#                             ),
#
#                             dbc.Button([
#                                 html.I(className="fas fa-info-circle me-1"),
#                                 "Details"
#                             ],
#                                 id={"type": "view-details-btn", "index": sample_set.id},
#                                 color="outline-info",
#                                 size="sm")
#                         ], size="sm")
#                     ], className="text-end")
#                 ], md=3)
#             ])
#         ])
#     ], className="shadow-sm mb-3")
#
#
# def create_analysis_badge(analysis_type, status):
#     """Create a small badge showing analysis status"""
#     status_config = {
#         'not_requested': {'color': 'light', 'icon': 'fa-circle'},
#         'requested': {'color': 'warning', 'icon': 'fa-clock'},
#         'in_progress': {'color': 'info', 'icon': 'fa-spinner fa-spin'},
#         'completed': {'color': 'success', 'icon': 'fa-check'}
#     }
#
#     config = status_config.get(status, status_config['not_requested'])
#
#     return dbc.Badge([
#         html.I(className=f"fas {config['icon']} me-1", style={"fontSize": "0.7rem"}),
#         analysis_type
#     ], color=config['color'], className="me-1", style={"fontSize": "0.75rem"})
#
#
# def create_analysis_request_modal():
#     """Create modal for requesting analyses"""
#     return dbc.Modal([
#         dbc.ModalHeader([
#             html.H5("Request Analysis", className="text-primary")
#         ]),
#         dbc.ModalBody([
#             html.Div(id="modal-sample-set-info", className="mb-3"),
#             html.Hr(),
#             html.H6("Select Analyses to Request:"),
#             dbc.Checklist(
#                 id="analysis-type-checklist",
#                 options=[
#                     {"label": "SEC - Size Exclusion Chromatography", "value": "SEC"},
#                     {"label": "Titer - Protein Concentration", "value": "Titer"},
#                     {"label": "CE-SDS - Capillary Electrophoresis", "value": "CE-SDS"},
#                     {"label": "cIEF - Isoelectric Focusing", "value": "cIEF"},
#                     {"label": "Mass Check - Mass Spectrometry", "value": "Mass Check"},
#                     {"label": "Glycan - Glycan Analysis", "value": "Glycan"},
#                     {"label": "HCP - Host Cell Protein", "value": "HCP"},
#                     {"label": "ProA - Protein A", "value": "ProA"}
#                 ],
#                 value=[],
#                 className="mb-3"
#             ),
#             html.Div([
#                 html.Label("Priority", className="fw-bold"),
#                 dbc.RadioItems(
#                     id="analysis-priority",
#                     options=[
#                         {"label": "Normal", "value": 1},
#                         {"label": "High", "value": 2},
#                         {"label": "Urgent", "value": 3}
#                     ],
#                     value=1,
#                     inline=True
#                 )
#             ], className="mb-3"),
#             html.Div([
#                 html.Label("Notes", className="fw-bold"),
#                 dbc.Textarea(
#                     id="analysis-notes",
#                     placeholder="Add any special instructions...",
#                     rows=3
#                 )
#             ])
#         ]),
#         dbc.ModalFooter([
#             dbc.Button("Cancel", id="cancel-analysis-request", color="secondary"),
#             dbc.Button([
#                 html.I(className="fas fa-paper-plane me-2"),
#                 "Submit Request"
#             ], id="submit-analysis-request", color="primary")
#         ])
#     ], id="analysis-request-modal", size="lg")
#
#
# def create_sample_set_details_modal():
#     """Create modal for viewing sample set details"""
#     return dbc.Modal([
#         dbc.ModalHeader([
#             html.H5("Sample Set Details", className="text-primary")
#         ]),
#         dbc.ModalBody([
#             html.Div(id="modal-sample-set-details")
#         ]),
#         dbc.ModalFooter([
#             dbc.Button("Close", id="close-details-modal", color="secondary")
#         ])
#     ], id="sample-set-details-modal", size="xl")

# cld_dashboard/samples/layouts/sample_sets.py - COMPLETE VERSION WITH SEC EMBEDDING

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

# Make sure this import path is correct for your project structure
try:
    from ...shared.styles.common_styles import CARD_STYLE, COLORS
    from ...shared.utils.url_helpers import build_sec_report_url
except ImportError:
    # Fallback if import fails
    CARD_STYLE = {}
    COLORS = {}
    print("Warning: Could not import common_styles or url_helpers")


def create_sample_sets_layout():
    """Create the sample sets management page"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-layer-group text-primary me-2"),
                    "Sample Sets Analysis Management"
                ]),
                html.P("Manage analysis requests and track progress for grouped samples",
                       className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-sample-sets-btn", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-file-export me-1"),
                        "Export"
                    ], id="export-sample-sets-btn", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Metrics Row
        dbc.Row([
            dbc.Col([
                create_metric_card("Total Sets", "0", "fa-layer-group", "primary", "total-sets-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("Pending Analysis", "0", "fa-clock", "warning", "pending-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("In Progress", "0", "fa-spinner", "info", "in-progress-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("Completed", "0", "fa-check-circle", "success", "completed-metric")
            ], md=3)
        ], className="mb-4"),

        # Filter Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Search", className="fw-bold small"),
                                dbc.Input(
                                    id="search-sample-sets",
                                    placeholder="Search by project, SIP, or stage...",
                                    type="text"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Project Filter", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="project-filter",
                                    options=[{"label": "All Projects", "value": "all"}],
                                    value="all",
                                    clearable=False
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Status Filter", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="status-filter",
                                    options=[
                                        {"label": "All Status", "value": "all"},
                                        {"label": "Has Pending", "value": "pending"},
                                        {"label": "All Complete", "value": "complete"},
                                        {"label": "No Analysis", "value": "none"}
                                    ],
                                    value="all",
                                    clearable=False
                                )
                            ], md=4)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Sample Sets Grid
        dbc.Row([
            dbc.Col([
                html.Div(id="sample-sets-grid", children=[
                    dbc.Spinner(
                        html.Div(style={"height": "200px"}),
                        color="primary"
                    )
                ])
            ])
        ]),

        # Analysis Request Modal
        create_analysis_request_modal(),

        # Sample Set Details Modal
        create_sample_set_details_modal(),

        # Toast notifications
        html.Div(id="sample-sets-notifications"),

        # Hidden stores
        dcc.Store(id="selected-sample-set", data={}),
        dcc.Store(id="available-projects", data=[]),

        # Dummy output for callbacks that don't need real output
        html.Div(id="dummy-output", style={"display": "none"})

    ], fluid=True, style={"padding": "20px"})


def create_metric_card(title, metric_id, icon, color, card_id):
    """Create a metric display card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H3("0", id=card_id, className=f"text-{color} mb-0"),
                    html.P(title, className="text-muted mb-0 small")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color} opacity-75")
                ], className="align-self-center")
            ], className="d-flex")
        ])
    ], className="shadow-sm h-100")


def create_sample_set_card(sample_set, analysis_status):
    """Create a card for a single sample set with SEC embedding"""
    # Determine overall status
    has_pending = any(status == 'requested' for status in analysis_status.values())
    has_in_progress = any(status == 'in_progress' for status in analysis_status.values())
    all_complete = all(status == 'completed' for status in analysis_status.values()
                       if status != 'not_requested')

    if has_pending:
        overall_status = {"color": "warning", "icon": "fa-clock", "text": "Pending"}
    elif has_in_progress:
        overall_status = {"color": "info", "icon": "fa-spinner", "text": "In Progress"}
    elif all_complete and any(status == 'completed' for status in analysis_status.values()):
        overall_status = {"color": "success", "icon": "fa-check-circle", "text": "Completed"}
    else:
        overall_status = {"color": "secondary", "icon": "fa-circle", "text": "No Analysis"}

    # Get sample IDs for this set
    sample_ids = [member.sample.sample_id for member in sample_set.members.all()]

    # Check for existing SEC reports
    from plotly_integration.models import Report
    sec_reports = Report.objects.filter(
        analysis_type=1,  # SEC
        project_id=sample_set.project_id
    ).order_by('-date_created')

    # Build SEC button with proper URL
    if sample_ids:
        # Check if SEC reports exist for this project
        if sec_reports.exists():
            latest_report = sec_reports.first()
            # If report exists, use report_id
            sec_embed_url = f"#!/analysis/sec/report?report_id={latest_report.report_id}"
            sec_button_text = "View SEC Report"
            sec_button_color = "success"
        else:
            # No reports yet - for now just open SEC app
            # Later we'll add functionality to create reports with pre-selected samples
            sec_embed_url = "#!/analysis/sec"
            sec_button_text = "Create SEC Report"
            sec_button_color = "outline-success"
    else:
        # No samples - just open SEC app
        sec_embed_url = "#!/analysis/sec"
        sec_button_text = "Open SEC App"
        sec_button_color = "outline-secondary"

    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Left section: Basic info
                dbc.Col([
                    html.Div([
                        html.H5(sample_set.set_name, className="mb-1"),
                        html.P([
                            html.I(className="fas fa-vial text-primary me-2"),
                            f"{sample_set.sample_count} samples",
                            html.Span(" | ", className="text-muted"),
                            html.I(className="fas fa-calendar text-info me-2"),
                            f"Created: {sample_set.created_at.strftime('%Y-%m-%d')}" if sample_set.created_at else "Unknown"
                        ], className="mb-2 text-muted small"),
                        # Show sample IDs preview
                        html.P([
                            html.Strong("Samples: "),
                            ", ".join(sample_ids[:3]) + ("..." if len(sample_ids) > 3 else "")
                        ], className="text-muted small mb-0")
                    ])
                ], md=3),

                # Middle section: Analysis badges
                dbc.Col([
                    html.Div([
                        html.P("Analysis Status:", className="fw-bold small mb-2"),
                        html.Div([
                            create_analysis_badge(analysis_type, status)
                            for analysis_type, status in analysis_status.items()
                        ], className="d-flex flex-wrap gap-1")
                    ])
                ], md=6),

                # Right section: Actions and overall status
                dbc.Col([
                    html.Div([
                        dbc.Badge([
                            html.I(className=f"fas {overall_status['icon']} me-1"),
                            overall_status['text']
                        ], color=overall_status['color'], className="mb-2"),

                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-microscope me-1"),
                                "Request Analysis"
                            ],
                                id={"type": "request-analysis-btn", "index": sample_set.id},
                                color="primary",
                                size="sm"),

                            # SEC button - properly configured with embedded URL
                            dbc.Button([
                                html.I(className="fas fa-chart-line me-1"),
                                sec_button_text
                            ],
                                href=sec_embed_url,  # Use hash routing to embedded SEC
                                color=sec_button_color,
                                size="sm",
                                disabled=False,
                                id={"type": "sec-embed-btn", "index": sample_set.id}  # Add ID for debugging
                            ),

                            dbc.Button([
                                html.I(className="fas fa-info-circle me-1"),
                                "Details"
                            ],
                                id={"type": "view-details-btn", "index": sample_set.id},
                                color="outline-info",
                                size="sm")
                        ], size="sm")
                    ], className="text-end")
                ], md=3)
            ])
        ])
    ], className="shadow-sm mb-3")


def create_analysis_badge(analysis_type, status):
    """Create a small badge showing analysis status"""
    status_config = {
        'not_requested': {'color': 'light', 'icon': 'fa-circle'},
        'requested': {'color': 'warning', 'icon': 'fa-clock'},
        'in_progress': {'color': 'info', 'icon': 'fa-spinner fa-spin'},
        'completed': {'color': 'success', 'icon': 'fa-check'}
    }

    config = status_config.get(status, status_config['not_requested'])

    return dbc.Badge([
        html.I(className=f"fas {config['icon']} me-1", style={"fontSize": "0.7rem"}),
        analysis_type
    ], color=config['color'], className="me-1", style={"fontSize": "0.75rem"})


def create_analysis_request_modal():
    """Create modal for requesting analyses"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Request Analysis", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div(id="modal-sample-set-info", className="mb-3"),
            html.Hr(),
            html.H6("Select Analyses to Request:"),
            dbc.Checklist(
                id="analysis-type-checklist",
                options=[
                    {"label": "SEC - Size Exclusion Chromatography", "value": "SEC"},
                    {"label": "Titer - Protein Concentration", "value": "Titer"},
                    {"label": "CE-SDS - Capillary Electrophoresis", "value": "CE-SDS"},
                    {"label": "cIEF - Isoelectric Focusing", "value": "cIEF"},
                    {"label": "Mass Check - Mass Spectrometry", "value": "Mass Check"},
                    {"label": "Glycan - Glycan Analysis", "value": "Glycan"},
                    {"label": "HCP - Host Cell Protein", "value": "HCP"},
                    {"label": "ProA - Protein A", "value": "ProA"}
                ],
                value=[],
                className="mb-3"
            ),
            html.Div([
                html.Label("Priority", className="fw-bold"),
                dbc.RadioItems(
                    id="analysis-priority",
                    options=[
                        {"label": "Normal", "value": 1},
                        {"label": "High", "value": 2},
                        {"label": "Urgent", "value": 3}
                    ],
                    value=1,
                    inline=True
                )
            ], className="mb-3"),
            html.Div([
                html.Label("Notes", className="fw-bold"),
                dbc.Textarea(
                    id="analysis-notes",
                    placeholder="Add any special instructions...",
                    rows=3
                )
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-analysis-request", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-paper-plane me-2"),
                "Submit Request"
            ], id="submit-analysis-request", color="primary")
        ])
    ], id="analysis-request-modal", size="lg")


def create_sample_set_details_modal():
    """Create modal for viewing sample set details"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Sample Set Details", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div(id="modal-sample-set-details")
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-details-modal", color="secondary")
        ])
    ], id="sample-set-details-modal", size="xl")


def create_sec_button_with_samples(sample_ids, sample_set_name, existing_reports=None):
    """Create SEC button that properly embeds the SEC app with selected samples

    Args:
        sample_ids: List of sample IDs to analyze
        sample_set_name: Name of the sample set
        existing_reports: QuerySet of existing reports for this project
    """
    if not sample_ids:
        return dbc.Button([
            html.I(className="fas fa-chart-line me-1"),
            "No Samples"
        ], color="secondary", size="sm", disabled=True)

    # Build the embedded URL with sample IDs
    samples_param = ",".join(str(sid) for sid in sample_ids)

    # Use hash routing to embedded SEC report
    if existing_reports and existing_reports.exists():
        # If reports exist, show the latest one
        latest_report = existing_reports.first()
        embed_url = f"#!/analysis/sec/report?samples={samples_param}&report_id={latest_report.report_id}&mode=report"
        button_text = "View SEC Report"
        button_color = "success"
    else:
        # No reports yet - create new
        embed_url = f"#!/analysis/sec/report?samples={samples_param}&mode=samples"
        button_text = "Create SEC Report"
        button_color = "primary"

    return dbc.Button([
        html.I(className="fas fa-chart-line me-1"),
        button_text
    ],
        href=embed_url,
        color=button_color,
        size="sm",
        title=f"SEC analysis for {sample_set_name}"
    )


def build_sec_embed_url(sample_set=None, report_id=None):
    """
    Build the URL for embedded SEC analysis

    Args:
        sample_set: Optional sample set object (for future use)
        report_id: Report ID to view

    Returns:
        str: Hash-based URL for embedded SEC view
    """
    if report_id:
        return f"#!/analysis/sec/report?report_id={report_id}"
    else:
        # No report - just go to SEC dashboard
        return "#!/analysis/sec"


def get_sec_button_config(sample_set):
    """Get configuration for SEC button based on sample set"""
    # Get sample IDs (for display purposes)
    sample_ids = [member.sample.sample_id for member in sample_set.members.all()]

    if not sample_ids:
        return {
            "url": "#!/analysis/sec",
            "text": "No Samples",
            "color": "secondary",
            "disabled": True
        }

    # Check for existing reports
    from plotly_integration.models import Report
    sec_reports = Report.objects.filter(
        analysis_type=1,  # SEC
        project_id=sample_set.project_id
    ).order_by('-date_created')

    if sec_reports.exists():
        latest_report = sec_reports.first()
        return {
            "url": build_sec_embed_url(report_id=latest_report.report_id),
            "text": f"View SEC Report #{latest_report.report_id}",
            "color": "success",
            "disabled": False
        }
    else:
        return {
            "url": "#!/analysis/sec",
            "text": "Create SEC Report",
            "color": "primary",
            "disabled": False
        }


# TABLE VIEW FUNCTIONS (if needed)
def create_sample_sets_table_layout():
    """Create table view of sample sets"""
    return dbc.Container([
        html.H2("Sample Sets - Table View"),
        html.P("Table view of all sample sets"),
        # Add table implementation here
    ], fluid=True, style={"padding": "20px"})


def create_sample_set_detail_layout(query_params):
    """Create detailed view of a single sample set"""
    sample_set_id = query_params.get('id', [''])[0]

    return dbc.Container([
        html.H2(f"Sample Set Details - ID: {sample_set_id}"),
        html.P("Detailed view will be implemented here"),
        dbc.Button("Back to Sample Sets", href="#!/sample-sets", color="secondary")
    ], fluid=True, style={"padding": "20px"})