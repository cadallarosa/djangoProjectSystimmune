# Enhanced sample_sets.py with modern UI components
import dash
from dash import html, dcc, dash_table, callback, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from ...shared.styles.common_styles import TABLE_STYLE_CELL, TABLE_STYLE_HEADER, CARD_STYLE, COLORS
from ...config.analysis_types import ANALYSIS_TYPES, STATUS_COLORS, STATUS_ICONS
import json


def create_sample_sets_overview_layout():
    """Create the enhanced sample sets overview page with modern UI"""
    return dbc.Container([
        # Enhanced header with search and filters
        dbc.Row([
            dbc.Col([
                html.H2("🧪 Sample Set Analytics", className="text-primary mb-1"),
                html.P("Advanced sample grouping and intelligent analysis", className="text-muted")
            ], md=6),
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText(html.I(className="fas fa-search")),
                    dbc.Input(
                        id="sample-sets-search",
                        placeholder="Search sample sets...",
                        type="text"
                    ),
                    dbc.Button("Search", color="primary", outline=True)
                ], size="sm")
            ], md=6)
        ], className="mb-4"),

        # Advanced controls and metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Grouping Method", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="grouping-method",
                                    options=[
                                        {"label": "🔬 By Project + SIP", "value": "project_sip"},
                                        {"label": "📅 By Date Range", "value": "date_range"},
                                        {"label": "👨‍🔬 By Analyst", "value": "analyst"},
                                        {"label": "🧬 By Clone", "value": "clone"},
                                        {"label": "🤖 Auto-Detect", "value": "auto"}
                                    ],
                                    value="project_sip",
                                    clearable=False,
                                    style={"fontSize": "14px"}
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Analysis Status", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="status-filter",
                                    options=[
                                        {"label": "🔍 All Status", "value": "all"},
                                        {"label": "⚠️ Pending Analysis", "value": "pending"},
                                        {"label": "🟡 In Progress", "value": "in_progress"},
                                        {"label": "✅ Completed", "value": "completed"},
                                        {"label": "❌ Failed", "value": "failed"}
                                    ],
                                    value="all",
                                    clearable=False,
                                    style={"fontSize": "14px"}
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("View Mode", className="fw-bold small"),
                                dbc.RadioItems(
                                    id="view-mode",
                                    options=[
                                        {"label": "Grid", "value": "grid"},
                                        {"label": "Table", "value": "table"},
                                        {"label": "Timeline", "value": "timeline"}
                                    ],
                                    value="grid",
                                    inline=True,
                                    style={"fontSize": "14px"}
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Quick Actions", className="fw-bold small"),
                                dbc.ButtonGroup([
                                    dbc.Button([
                                        html.I(className="fas fa-sync-alt me-1"),
                                        "Refresh"
                                    ], id="refresh-sample-sets-btn", color="outline-primary", size="sm"),
                                    dbc.Button([
                                        html.I(className="fas fa-magic me-1"),
                                        "Auto-Group"
                                    ], id="auto-group-btn", color="outline-info", size="sm")
                                ])
                            ], md=3)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Metrics overview cards
        dbc.Row([
            dbc.Col([
                create_metric_card("Total Sets", "0", "fa-layer-group", "primary", "total-sets-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("Pending Analysis", "0", "fa-clock", "warning", "pending-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("Completed", "0", "fa-check-circle", "success", "completed-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("Total Samples", "0", "fa-vial", "info", "total-samples-metric")
            ], md=3)
        ], className="mb-4"),

        # Main content area with view switching
        dbc.Row([
            dbc.Col([
                html.Div(id="sample-sets-content-area")
            ])
        ]),

        # Batch operations panel
        dbc.Row([
            dbc.Col([
                dbc.Collapse([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6("🚀 Batch Operations", className="mb-0")
                        ]),
                        dbc.CardBody([
                            create_batch_operations_panel()
                        ])
                    ], className="shadow-sm")
                ], id="batch-operations-collapse", is_open=False)
            ])
        ], className="mt-3"),

        # Modals and hidden components
        create_sample_set_preview_modal(),
        create_comparison_modal(),
        dcc.Store(id="selected-sample-sets", data=[]),
        dcc.Store(id="sample-sets-data", data=[]),
        html.Div(id="sample-sets-notifications")

    ], fluid=True, style={"padding": "20px"})


def create_metric_card(title, value_id, icon, color, metric_id):
    """Create an enhanced metric card with animations"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4("0", id=metric_id, className=f"text-{color} mb-0 metric-value"),
                    html.P(title, className="text-muted mb-0 fw-bold small"),
                    html.Div(id=f"{metric_id}-trend", className="trend-indicator")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color} opacity-75")
                ], className="align-self-center")
            ], className="d-flex"),
            dbc.Progress(
                id=f"{metric_id}-progress",
                value=0,
                color=color,
                style={"height": "3px", "marginTop": "8px"},
                className="progress-bar-animated"
            )
        ])
    ], className="shadow-sm card-hover h-100")


def create_sample_sets_grid_view(sample_sets_data):
    """Create modern grid view of sample sets"""
    if not sample_sets_data:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No sample sets found. Adjust your filters or create some samples."
        ], color="info")

    grid_cards = []
    for i in range(0, len(sample_sets_data), 3):  # 3 cards per row
        row_cards = sample_sets_data[i:i + 3]
        grid_cards.append(
            dbc.Row([
                dbc.Col([
                    create_enhanced_sample_set_card(card_data, index=i + j)
                ], md=4) for j, card_data in enumerate(row_cards)
            ], className="mb-3")
        )

    return html.Div(grid_cards)


def create_enhanced_sample_set_card(set_data, index=0):
    """Create an enhanced sample set card with modern design"""
    set_name = set_data.get('set_name', 'Unknown Set')
    project = set_data.get('project', '')
    sip = set_data.get('sip_number', '')
    stage = set_data.get('development_stage', '')
    sample_count = set_data.get('sample_count', 0)
    sec_status = set_data.get('sec_status', 'No Analysis')
    sample_ids = set_data.get('sample_ids', [])

    # Enhanced status styling
    status_config = get_status_config(sec_status)

    return dbc.Card([
        # Card header with status indicator
        dbc.CardHeader([
            html.Div([
                html.Div([
                    html.H6(set_name, className="mb-0 text-truncate"),
                    html.Small(f"{sample_count} samples", className="text-muted")
                ], className="flex-grow-1"),
                dbc.Badge([
                    html.I(className=f"fas {status_config['icon']} me-1"),
                    sec_status
                ], color=status_config['color'], className="status-badge")
            ], className="d-flex align-items-center")
        ], className="bg-light"),

        # Card body with details
        dbc.CardBody([
            # Project details
            html.Div([
                html.P([
                    html.I(className="fas fa-project-diagram text-primary me-2"),
                    html.Strong("Project: "), project
                ], className="small mb-1"),
                html.P([
                    html.I(className="fas fa-hashtag text-info me-2"),
                    html.Strong("SIP: "), sip or "N/A"
                ], className="small mb-1"),
                html.P([
                    html.I(className="fas fa-flask text-success me-2"),
                    html.Strong("Stage: "), stage or "N/A"
                ], className="small mb-2")
            ]),

            # Mini preview chart
            html.Div([
                create_mini_preview_chart(sample_ids),
            ], className="mb-3"),

            # Action buttons
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-eye me-1"),
                    "View"
                ],
                    id={"type": "view-set-btn", "index": index},
                    color="outline-primary",
                    size="sm"),
                dbc.Button([
                    html.I(className="fas fa-microscope me-1"),
                    "Analyze"
                ],
                    id={"type": "analyze-set-btn", "index": index},
                    color="primary" if sec_status == "No Analysis" else "outline-success",
                    size="sm"),
                dbc.Button([
                    html.I(className="fas fa-chart-line me-1")
                ],
                    id={"type": "preview-set-btn", "index": index},
                    color="outline-info",
                    size="sm",
                    title="Quick Preview")
            ], size="sm", className="w-100"),

            # Selection checkbox
            dbc.Checklist(
                id={"type": "select-set-checkbox", "index": index},
                options=[{"label": "", "value": set_name}],
                value=[],
                className="mt-2"
            )
        ])
    ], className="shadow-sm card-hover sample-set-card", style={"minHeight": "350px"})


def create_mini_preview_chart(sample_ids):
    """Create a mini preview chart for sample set"""
    # Mock data for preview - replace with actual SEC data
    if not sample_ids:
        return html.Div("No data", className="text-muted text-center py-2")

    # Create simple line chart
    fig = go.Figure()

    # Mock chromatogram data
    x_data = list(range(0, 20))
    for i, sample_id in enumerate(sample_ids[:3]):  # Show first 3 samples
        y_data = [0.1 + 0.05 * (i % 3) + 0.8 * (1 if 8 <= x <= 12 else 0.1) for x in x_data]
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines',
            name=sample_id,
            line=dict(width=1.5),
            showlegend=False
        ))

    fig.update_layout(
        height=80,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_sample_sets_table_view(sample_sets_data):
    """Create enhanced table view with modern styling"""
    if not sample_sets_data:
        return dbc.Alert("No sample sets found", color="info")

    return dash_table.DataTable(
        id="sample-sets-table-enhanced",
        columns=[
            {"name": "Select", "id": "select", "type": "text", "presentation": "markdown"},
            {"name": "Project", "id": "project", "type": "text"},
            {"name": "Set Name", "id": "set_name", "type": "text"},
            {"name": "SIP #", "id": "sip_number", "type": "text"},
            {"name": "Stage", "id": "development_stage", "type": "text"},
            {"name": "Samples", "id": "sample_count", "type": "numeric"},
            {"name": "Status", "id": "sec_status", "type": "text", "presentation": "markdown"},
            {"name": "Progress", "id": "progress", "type": "text", "presentation": "markdown"},
            {"name": "Actions", "id": "actions", "type": "text", "presentation": "markdown"}
        ],
        data=prepare_table_data(sample_sets_data),
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_size=15,
        style_cell={
            **TABLE_STYLE_CELL,
            'minWidth': '100px',
            'maxWidth': '200px',
            'whiteSpace': 'normal'
        },
        style_header={
            **TABLE_STYLE_HEADER,
            'backgroundColor': '#495057',
            'color': 'white'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{sec_status} contains "Completed"'},
                'backgroundColor': '#d4edda',
                'color': '#155724'
            },
            {
                'if': {'filter_query': '{sec_status} contains "Pending"'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            },
            {
                'if': {'filter_query': '{sec_status} contains "Progress"'},
                'backgroundColor': '#d1ecf1',
                'color': '#0c5460'
            }
        ],
        style_table={'overflowX': 'auto'},
        markdown_options={"link_target": "_blank"}
    )


def create_timeline_view(sample_sets_data):
    """Create timeline view of sample sets"""
    if not sample_sets_data:
        return dbc.Alert("No sample sets found", color="info")

    # Create timeline scatter plot
    fig = go.Figure()

    for set_data in sample_sets_data:
        fig.add_trace(go.Scatter(
            x=[f"2024-01-{hash(set_data['set_name']) % 30 + 1:02d}"],  # Mock dates
            y=[set_data['project']],
            mode='markers+text',
            marker=dict(
                size=set_data['sample_count'] * 2,
                color=get_status_color(set_data['sec_status']),
                line=dict(width=2, color='white')
            ),
            text=set_data['set_name'],
            textposition="top center",
            name=set_data['set_name'],
            hovertemplate=f"<b>{set_data['set_name']}</b><br>" +
                          f"Project: {set_data['project']}<br>" +
                          f"Samples: {set_data['sample_count']}<br>" +
                          f"Status: {set_data['sec_status']}<extra></extra>"
        ))

    fig.update_layout(
        title="Sample Sets Timeline",
        xaxis_title="Date",
        yaxis_title="Project",
        height=500,
        showlegend=False,
        hovermode='closest'
    )

    return dcc.Graph(figure=fig)


def create_batch_operations_panel():
    """Create batch operations panel"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H6("Selected Sets", className="text-muted"),
                html.Div(id="selected-sets-display", children=[
                    html.P("No sets selected", className="text-muted small")
                ])
            ], md=4),
            dbc.Col([
                html.H6("Available Operations", className="text-muted"),
                dbc.Checklist(
                    id="batch-operations-checklist",
                    options=[
                        {"label": "🔬 Create SEC Reports", "value": "create_sec"},
                        {"label": "📊 Generate Analytics", "value": "generate_analytics"},
                        {"label": "📤 Export Data", "value": "export_data"},
                        {"label": "🔗 Link LIMS Data", "value": "link_lims"}
                    ],
                    value=[],
                    className="small"
                )
            ], md=4),
            dbc.Col([
                html.H6("Execute", className="text-muted"),
                dbc.Button([
                    html.I(className="fas fa-rocket me-2"),
                    "Run Operations"
                ], id="execute-batch-btn", color="success", disabled=True, className="w-100"),
                html.Div(id="batch-execution-status", className="mt-2")
            ], md=4)
        ])
    ])


def create_sample_set_preview_modal():
    """Create modal for sample set preview"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4("Sample Set Preview", className="text-primary")
        ]),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Set Information"),
                    html.Div(id="preview-set-info")
                ], md=4),
                dbc.Col([
                    html.H6("SEC Chromatogram Preview"),
                    dcc.Graph(id="preview-chromatogram", style={"height": "300px"})
                ], md=8)
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H6("Sample Details"),
                    html.Div(id="preview-sample-details")
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-preview-modal", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-microscope me-2"),
                "Open SEC Analysis"
            ], id="open-sec-from-preview", color="primary")
        ])
    ], id="sample-set-preview-modal", size="xl")


def create_comparison_modal():
    """Create modal for comparing sample sets"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4("Compare Sample Sets", className="text-primary")
        ]),
        dbc.ModalBody([
            html.P("Select 2-4 sample sets to compare:", className="text-muted"),
            html.Div(id="comparison-selection"),
            html.Hr(),
            html.Div(id="comparison-charts")
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-comparison-modal", color="secondary"),
            dbc.Button("Generate Report", id="generate-comparison-report", color="info")
        ])
    ], id="comparison-modal", size="xl")


def prepare_table_data(sample_sets_data):
    """Prepare data for table view with enhanced formatting"""
    table_data = []

    for i, set_data in enumerate(sample_sets_data):
        # Create checkbox for selection
        select_checkbox = f"☐"  # Will be handled by callback

        # Create status badge
        status_config = get_status_config(set_data['sec_status'])
        status_badge = f"<span style='color: {status_config['color_code']}'>" + \
                       f"<i class='fas {status_config['icon']}'></i> {set_data['sec_status']}</span>"

        # Create progress indicator
        if set_data['sec_status'] == 'Completed':
            progress = "![100%](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjIwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjIwIiBmaWxsPSIjMjhhNzQ1Ii8+PC9zdmc+)"
        elif 'Progress' in set_data['sec_status']:
            progress = "![50%](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjIwIj48cmVjdCB3aWR0aD0iNTAiIGhlaWdodD0iMjAiIGZpbGw9IiNmZmMxMDciLz48L3N2Zz4=)"
        else:
            progress = "![0%](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjIwIj48cmVjdCB3aWR0aD0iNSIgaGVpZ2h0PSIyMCIgZmlsbD0iIzZjNzU3ZCIvPjwvc3ZnPg==)"

        # Create action buttons
        actions = f"[👁️ View](#!/sample-sets/view?project={set_data['project']}) | " + \
                  f"[🔬 Analyze](#!/analysis/sec?samples={','.join(set_data.get('sample_ids', []))}) | " + \
                  f"[📊 Preview](#)"

        table_data.append({
            "select": select_checkbox,
            "project": set_data['project'],
            "set_name": set_data['set_name'],
            "sip_number": set_data.get('sip_number', ''),
            "development_stage": set_data.get('development_stage', ''),
            "sample_count": set_data['sample_count'],
            "sec_status": status_badge,
            "progress": progress,
            "actions": actions
        })

    return table_data


def get_status_config(status):
    """Get configuration for status display"""
    status_configs = {
        'No Analysis': {
            'color': 'secondary',
            'color_code': '#6c757d',
            'icon': 'fa-clock'
        },
        'Pending': {
            'color': 'warning',
            'color_code': '#ffc107',
            'icon': 'fa-hourglass-half'
        },
        'In Progress': {
            'color': 'info',
            'color_code': '#17a2b8',
            'icon': 'fa-spinner'
        },
        'Completed': {
            'color': 'success',
            'color_code': '#28a745',
            'icon': 'fa-check-circle'
        },
        'Failed': {
            'color': 'danger',
            'color_code': '#dc3545',
            'icon': 'fa-times-circle'
        }
    }

    return status_configs.get(status, status_configs['No Analysis'])


def get_status_color(status):
    """Get color for status in charts"""
    color_map = {
        'No Analysis': '#6c757d',
        'Pending': '#ffc107',
        'In Progress': '#17a2b8',
        'Completed': '#28a745',
        'Failed': '#dc3545'
    }
    return color_map.get(status, '#6c757d')


# Enhanced callbacks for the sample sets page
@callback(
    [Output("sample-sets-content-area", "children"),
     Output("total-sets-metric", "children"),
     Output("pending-metric", "children"),
     Output("completed-metric", "children"),
     Output("total-samples-metric", "children")],
    [Input("view-mode", "value"),
     Input("grouping-method", "value"),
     Input("status-filter", "value"),
     Input("refresh-sample-sets-btn", "n_clicks"),
     Input("auto-group-btn", "n_clicks")],
    [State("sample-sets-search", "value")]
)
def update_sample_sets_content(view_mode, grouping_method, status_filter, refresh_clicks,
                               auto_clicks, search_term):
    """Update sample sets content based on user selections"""
    try:
        # Mock data - replace with actual database queries
        sample_sets_data = [
            {
                "set_name": "PROJ001_SIP001_MP",
                "project": "PROJ001",
                "sip_number": "SIP001",
                "development_stage": "MP",
                "sample_count": 20,
                "sec_status": "Completed",
                "sample_ids": [f"FB{1000 + i}" for i in range(20)]
            },
            {
                "set_name": "PROJ002_SIP002_BP",
                "project": "PROJ002",
                "sip_number": "SIP002",
                "development_stage": "BP",
                "sample_count": 15,
                "sec_status": "In Progress",
                "sample_ids": [f"FB{1020 + i}" for i in range(15)]
            },
            {
                "set_name": "PROJ003_SIP003_pMP",
                "project": "PROJ003",
                "sip_number": "SIP003",
                "development_stage": "pMP",
                "sample_count": 25,
                "sec_status": "Pending",
                "sample_ids": [f"FB{1035 + i}" for i in range(25)]
            }
        ]

        # Apply filters
        if status_filter != "all":
            if status_filter == "pending":
                sample_sets_data = [s for s in sample_sets_data if "Pending" in s["sec_status"]]
            elif status_filter == "completed":
                sample_sets_data = [s for s in sample_sets_data if "Completed" in s["sec_status"]]
            elif status_filter == "in_progress":
                sample_sets_data = [s for s in sample_sets_data if "Progress" in s["sec_status"]]

        # Apply search filter
        if search_term:
            sample_sets_data = [
                s for s in sample_sets_data
                if search_term.lower() in s["set_name"].lower() or
                   search_term.lower() in s["project"].lower()
            ]

        # Calculate metrics
        total_sets = len(sample_sets_data)
        pending_count = len([s for s in sample_sets_data if "Pending" in s["sec_status"]])
        completed_count = len([s for s in sample_sets_data if "Completed" in s["sec_status"]])
        total_samples = sum(s["sample_count"] for s in sample_sets_data)

        # Generate content based on view mode
        if view_mode == "grid":
            content = create_sample_sets_grid_view(sample_sets_data)
        elif view_mode == "table":
            content = create_sample_sets_table_view(sample_sets_data)
        else:  # timeline
            content = create_timeline_view(sample_sets_data)

        return (
            content,
            f"{total_sets:,}",
            f"{pending_count:,}",
            f"{completed_count:,}",
            f"{total_samples:,}"
        )

    except Exception as e:
        error_content = dbc.Alert(f"Error loading sample sets: {str(e)}", color="danger")
        return error_content, "Error", "Error", "Error", "Error"


@callback(
    Output("batch-operations-collapse", "is_open"),
    Input({"type": "select-set-checkbox", "index": ALL}, "value"),
    prevent_initial_call=True
)
def toggle_batch_operations(checkbox_values):
    """Show/hide batch operations based on selections"""
    selected_count = sum(len(val) for val in checkbox_values if val)
    return selected_count > 0


@callback(
    [Output("selected-sets-display", "children"),
     Output("execute-batch-btn", "disabled")],
    [Input({"type": "select-set-checkbox", "index": ALL}, "value"),
     Input("batch-operations-checklist", "value")]
)
def update_batch_operations_display(checkbox_values, selected_operations):
    """Update batch operations display"""
    selected_sets = []
    for i, val in enumerate(checkbox_values):
        if val:
            selected_sets.extend(val)

    if not selected_sets:
        return html.P("No sets selected", className="text-muted small"), True

    sets_display = html.Div([
        dbc.Badge(f"{len(selected_sets)} sets selected", color="primary"),
        html.Ul([
                    html.Li(set_name, className="small") for set_name in selected_sets[:5]
                ] + ([html.Li(f"... and {len(selected_sets) - 5} more", className="small text-muted")]
                     if len(selected_sets) > 5 else []))
    ])

    button_disabled = not selected_sets or not selected_operations

    return sets_display, button_disabled


@callback(
    Output("batch-execution-status", "children"),
    Input("execute-batch-btn", "n_clicks"),
    [State({"type": "select-set-checkbox", "index": ALL}, "value"),
     State("batch-operations-checklist", "value")],
    prevent_initial_call=True
)
def execute_batch_operations(n_clicks, checkbox_values, selected_operations):
    """Execute selected batch operations"""
    if not n_clicks:
        return ""

    selected_sets = []
    for val in checkbox_values:
        if val:
            selected_sets.extend(val)

    if not selected_sets or not selected_operations:
        return dbc.Alert("No sets or operations selected", color="warning", dismissable=True)

    # Mock execution - replace with actual operations
    results = []
    for operation in selected_operations:
        if operation == "create_sec":
            results.append(f"✅ Created SEC reports for {len(selected_sets)} sets")
        elif operation == "generate_analytics":
            results.append(f"📊 Generated analytics for {len(selected_sets)} sets")
        elif operation == "export_data":
            results.append(f"📤 Exported data for {len(selected_sets)} sets")
        elif operation == "link_lims":
            results.append(f"🔗 Linked LIMS data for {len(selected_sets)} sets")

    return dbc.Alert([
        html.H6("Batch Operations Completed", className="alert-heading"),
        html.Hr(),
        html.Ul([html.Li(result) for result in results])
    ], color="success", dismissable=True)


@callback(
    [Output("sample-set-preview-modal", "is_open"),
     Output("preview-set-info", "children"),
     Output("preview-chromatogram", "figure")],
    [Input({"type": "preview-set-btn", "index": ALL}, "n_clicks"),
     Input("close-preview-modal", "n_clicks")],
    prevent_initial_call=True
)
def handle_preview_modal(preview_clicks, close_clicks):
    """Handle sample set preview modal"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, "", go.Figure()

    trigger_id = ctx.triggered[0]["prop_id"]

    if "close-preview-modal" in trigger_id:
        return False, "", go.Figure()

    if "preview-set-btn" in trigger_id:
        # Mock preview data - replace with actual data
        set_info = html.Div([
            html.P([html.Strong("Project: "), "PROJ001"]),
            html.P([html.Strong("SIP: "), "SIP001"]),
            html.P([html.Strong("Stage: "), "MP"]),
            html.P([html.Strong("Samples: "), "20"]),
            html.P([html.Strong("Status: "),
                    dbc.Badge("Completed", color="success")])
        ])

        # Mock chromatogram
        fig = go.Figure()
        for i in range(3):
            x_data = list(range(0, 20))
            y_data = [0.1 + 0.8 * (1 if 8 <= x <= 12 else 0.1) for x in x_data]
            fig.add_trace(go.Scatter(
                x=x_data, y=y_data, mode='lines',
                name=f"Sample {i + 1}"
            ))

        fig.update_layout(
            title="SEC Chromatogram Preview",
            xaxis_title="Time (min)",
            yaxis_title="UV280 (mAU)"
        )

        return True, set_info, fig

    return False, "", go.Figure()


def create_sample_set_detail_layout(query_params):
    """Create enhanced detailed view for a specific sample set"""
    project = query_params.get('project', [''])[0]
    sip = query_params.get('sip', [''])[0]
    stage = query_params.get('stage', [''])[0]

    return dbc.Container([
        # Enhanced header with breadcrumbs
        dbc.Row([
            dbc.Col([
                dbc.Breadcrumb(items=[
                    {"label": "Sample Sets", "href": "#!/sample-sets"},
                    {"label": project, "active": True}
                ]),
                html.H2([
                    html.I(className="fas fa-layer-group text-primary me-2"),
                    f"Sample Set: {project}"
                ]),
                html.P(f"SIP: {sip} | Stage: {stage}" if sip or stage else "Sample set analysis",
                       className="text-muted lead")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-1"),
                        "Back"
                    ], href="#!/sample-sets", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-microscope me-1"),
                        "SEC Analysis"
                    ], id="request-sec-analysis-btn", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Export"
                    ], id="export-set-btn", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Enhanced info cards with metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 Sample Information"),
                    dbc.CardBody([
                        html.Div(id="sample-set-info")
                    ])
                ], className="shadow-sm")
            ], md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🔬 Analysis Status"),
                    dbc.CardBody([
                        html.Div(id="analysis-status-info")
                    ])
                ], className="shadow-sm")
            ], md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Quick Stats"),
                    dbc.CardBody([
                        html.Div(id="quick-stats-info")
                    ])
                ], className="shadow-sm")
            ], md=4)
        ], className="mb-4"),

        # Enhanced samples table with SEC preview
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5("Samples in Set", className="mb-0"),
                            html.Div([
                                dbc.Badge(id="sample-count-badge", color="primary"),
                                dbc.Button([
                                    html.I(className="fas fa-chart-line me-1"),
                                    "View All Chromatograms"
                                ], id="view-all-chromatograms-btn",
                                    color="outline-info", size="sm", className="ms-2")
                            ], className="float-end")
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id="samples-in-set-table")
                    ])
                ], className="shadow-sm")
            ])
        ])

    ], fluid=True, style={"padding": "20px"})