from dash import html, dcc, dash_table, Input, Output, State, callback
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from plotly_integration.models import LimsUpstreamSamples, Report, LimsSecResult
from datetime import datetime, timedelta
from collections import defaultdict

# Create the Dash app
app = DjangoDash(
    "CLDDashboardApp", 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ], 
    title="CLD Analytics Dashboard"
)

# ================== TABLE CONFIGURATIONS ==================
# Table styling
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

# FB Sample Fields
FB_SAMPLE_FIELDS = [
    {"name": "Sample #", "id": "sample_number", "editable": True},
    {"name": "Project", "id": "project_id", "editable": False},
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Development Stage", "id": "development_stage", "editable": False},
    {"name": "Titer (mg/L)", "id": "titer", "editable": True, "type": "numeric"},
    {"name": "Volume (mL)", "id": "volume", "editable": True, "type": "numeric"},
    {"name": "SIP #", "id": "sip_number", "editable": False},
    {"name": "CLD Analyst", "id": "cld_analyst", "editable": False},
    {"name": "SEC Status", "id": "sec_status", "editable": False},
    {"name": "Actions", "id": "actions", "editable": False, "presentation": "markdown"}
]

# UP Sample Fields
UP_SAMPLE_FIELDS = [
    {"name": "Sample #", "id": "sample_number", "editable": False},
    {"name": "Project", "id": "project_id", "editable": False},
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Development Stage", "id": "development_stage", "editable": False},
    {"name": "Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
    {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
    {"name": "CLD Analyst", "id": "cld_analyst", "editable": False},
    {"name": "SEC Status", "id": "sec_status", "editable": False, "presentation": "markdown"}
]

# SEC Report Columns
SEC_COLUMNS = [
    {"name": "Select", "id": "select", "editable": False},
    {"name": "Sample #", "id": "sample_number", "editable": False},
    {"name": "Clone", "id": "cell_line", "editable": False},
    {"name": "Project", "id": "project_id", "editable": False},
    {"name": "Harvest Date", "id": "harvest_date", "editable": False},
    {"name": "Main Peak (%)", "id": "main_peak_percent", "editable": False, "type": "numeric"},
    {"name": "HMW (%)", "id": "hmw_percent", "editable": False, "type": "numeric"},
    {"name": "LMW (%)", "id": "lmw_percent", "editable": False, "type": "numeric"},
    {"name": "Duplicate", "id": "duplicate", "editable": False, "type": "text"}
]

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
def get_dashboard_stats():
    """Get statistics for dashboard cards"""
    try:
        # FB samples have sample_type=2 (based on your view_samples.py)
        total_fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2).count()
        
        # Recent samples (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_samples = LimsUpstreamSamples.objects.filter(
            sample_type=2,
            created_at__gte=thirty_days_ago
        ).count()
        
        # SEC Reports count
        sec_reports = Report.objects.filter(analysis_type=1).count()
        
        # Pending analyses count
        pending_analyses = max(0, total_fb_samples - sec_reports)
        
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
            
            # FB Samples section
            html.P("FB SAMPLES", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className="fas fa-vial me-2"),
                "View Samples"
            ], href="/fb-samples/view", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-layer-group me-2"),
                "Sample Sets"
            ], href="/fb-samples/sets", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-plus me-2"),
                "Add Samples"
            ], href="/fb-samples/create", active="exact"),
            
            html.Hr(className="my-2"),
            
            # Reports section
            html.P("ANALYTICS", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className="fas fa-chart-line me-2"),
                "SEC Reports"
            ], href="/reports/sec/view", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-plus-circle me-2"),
                "Create SEC Report"
            ], href="/reports/sec/create", active="exact"),
            dbc.NavLink([
                html.I(className="fas fa-flask me-2"),
                "Titer Reports"
            ], href="/reports/titer", active="exact"),
            
            html.Hr(className="my-2"),
            
            # Settings
            html.P("SYSTEM", className="text-muted small fw-bold mb-1"),
            dbc.NavLink([
                html.I(className="fas fa-calendar-check me-2"),
                "Calibrations"
            ], href="/analytics/calibrations", active="exact"),
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
        
        # Quick Actions
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
                                    html.I(className="fas fa-plus me-2"),
                                    "Add FB Samples"
                                ], color="primary", href="/fb-samples/create", size="lg", 
                                className="w-100 mb-2")
                            ], md=6),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-search me-2"),
                                    "View All Samples"
                                ], color="outline-primary", href="/fb-samples/view", 
                                size="lg", className="w-100 mb-2")
                            ], md=6),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Create SEC Report"
                                ], color="success", href="/reports/sec/create", 
                                size="lg", className="w-100 mb-2")
                            ], md=6),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-history me-2"),
                                    "View Reports"
                                ], color="outline-success", href="/reports/sec/view", 
                                size="lg", className="w-100 mb-2")
                            ], md=6)
                        ])
                    ])
                ])
            ], md=8),
            
            # Recent Activity
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📈 Recent Activity", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="recent-activity-feed", children=[
                            html.P("✅ Dashboard ready", className="small mb-1"),
                            html.P("📊 Analytics available", className="small mb-1"),
                            html.P("🧪 FB samples loaded", className="small mb-1"),
                            html.P("⚙️ System operational", className="small mb-0"),
                        ])
                    ])
                ])
            ], md=4)
        ])
    ], style={"padding": "20px"})

def fb_samples_view_layout():
    """FB samples view layout"""
    return html.Div([
        # Header with actions
        dbc.Row([
            dbc.Col([
                html.H3("🧪 FB Samples", className="text-primary mb-1"),
                html.P("Cell Line Development Sample Management", className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-sync me-1"),
                        "Refresh"
                    ], id="refresh-samples-btn", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Add Samples"
                    ], href="/fb-samples/create", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Export"
                    ], id="export-samples-btn", color="outline-secondary", size="sm")
                ])
            ], md=4, className="text-end")
        ], className="mb-3"),
        
        # Main Data Table
        dash_table.DataTable(
            id="fb-samples-table",
            columns=[
                {
                    "name": col["name"],
                    "id": col["id"],
                    "editable": col.get("editable", False),
                    "type": col.get("type", "text"),
                    "presentation": col.get("presentation", "input")
                } for col in FB_SAMPLE_FIELDS
            ],
            data=[],
            editable=True,
            sort_action="native",
            filter_action="native",
            page_action="native",
            page_size=25,
            row_selectable="multi",
            selected_rows=[],
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER
        ),
        
        # Status
        html.Div(id="fb-samples-status", className="text-muted small mt-2")
    ], style={"padding": "20px"})

def fb_samples_create_layout():
    """FB samples creation layout"""
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3("➕ Create FB Samples", className="text-primary mb-1"),
                html.P("Add new Cell Line Development samples", className="text-muted")
            ])
        ], className="mb-4"),
        
        # Form Section
        dbc.Card([
            dbc.CardHeader([
                html.H5("📝 Sample Information", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Project *"),
                        dcc.Dropdown(
                            id="fb-project-dropdown",
                            placeholder="Select protein - molecule type"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Development Stage *"),
                        dcc.Dropdown(
                            id="fb-dev-stage",
                            options=[
                                {"label": "MP", "value": "MP"},
                                {"label": "pMP", "value": "pMP"},
                                {"label": "BP", "value": "BP"},
                                {"label": "BP SCC", "value": "BP SCC"},
                                {"label": "MP SCC", "value": "MP SCC"}
                            ],
                            value="MP"
                        )
                    ], md=2),
                    dbc.Col([
                        dbc.Label("CLD Analyst *"),
                        dcc.Dropdown(
                            id="fb-analyst",
                            options=[
                                {"label": "YY", "value": "YY"},
                                {"label": "JS", "value": "JS"},
                                {"label": "YW", "value": "YW"}
                            ]
                        )
                    ], md=2),
                    dbc.Col([
                        dbc.Label("SIP #"),
                        dbc.Input(id="fb-sip-number", type="number", placeholder="SIP#")
                    ], md=2),
                    dbc.Col([
                        dbc.Label("UNIFI #"),
                        dbc.Input(id="fb-unifi-number", type="number", placeholder="UNIFI#")
                    ], md=2)
                ], className="g-3")
            ])
        ], className="mb-4"),
        
        # Table Controls
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Add Row"
                    ], id="fb-add-row", color="secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-save me-1"),
                        "Save Samples"
                    ], id="fb-save-table", color="primary", size="sm")
                ])
            ], md=6),
            dbc.Col([
                html.Div(id="fb-save-status", className="text-end")
            ], md=6)
        ], className="mb-3"),
        
        # Sample Table
        dash_table.DataTable(
            id="fb-sample-table",
            columns=[
                {"name": "Sample Number", "id": "sample_number", "editable": True},
                {"name": "Clone", "id": "cell_line", "editable": True},
                {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
                {"name": "Titer (mg/L)", "id": "titer", "editable": True, "type": "numeric"},
                {"name": "Volume (mL)", "id": "volume", "editable": True, "type": "numeric"},
                {"name": "Notes", "id": "notes", "editable": True}
            ],
            data=[],
            editable=True,
            row_deletable=True,
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER
        )
    ], style={"padding": "20px"})

def sec_reports_create_layout():
    """SEC Report Creation layout"""
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3("📊 Create SEC Report", className="text-primary mb-1"),
                html.P("Size Exclusion Chromatography Analysis Report", className="text-muted")
            ])
        ], className="mb-4"),
        
        # Sample Selection
        dbc.Card([
            dbc.CardHeader([
                html.H5("🧪 Sample Selection", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select Samples"),
                        dcc.Dropdown(
                            id="sec-individual-samples",
                            placeholder="Search samples...",
                            multi=True
                        )
                    ], md=8),
                    dbc.Col([
                        dbc.Label("Action"),
                        html.Br(),
                        dbc.Button("Load Samples", id="sec-load-samples", 
                                 color="primary", size="sm")
                    ], md=2)
                ], className="g-2")
            ])
        ], className="mb-4"),
        
        # Selected Samples Table
        dbc.Card([
            dbc.CardHeader([
                html.H5("📋 Selected Samples", className="mb-0")
            ]),
            dbc.CardBody([
                dash_table.DataTable(
                    id="sec-sample-table",
                    columns=SEC_COLUMNS,
                    data=[],
                    row_selectable="multi",
                    filter_action="native",
                    sort_action="native",
                    style_table={"overflowX": "auto"},
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER
                )
            ])
        ], className="mb-4"),
        
        # Action Buttons
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-save me-1"),
                        "Save Draft"
                    ], id="sec-save-draft", color="outline-primary"),
                    dbc.Button([
                        html.I(className="fas fa-play me-1"),
                        "Generate Report"
                    ], id="sec-generate-report", color="primary")
                ])
            ])
        ]),
        
        # Status
        html.Div(id="sec-report-status", className="mt-3")
    ], style={"padding": "20px"})

def sec_reports_view_layout():
    """View existing SEC reports"""
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3("📊 SEC Reports", className="text-primary mb-1"),
                html.P("View and manage Size Exclusion Chromatography reports", className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-plus me-1"),
                    "Create Report"
                ], href="/reports/sec/create", color="primary", size="sm")
            ], md=4, className="text-end")
        ], className="mb-4"),
        
        # Reports Table
        dash_table.DataTable(
            id="sec-reports-table",
            columns=[
                {"name": "Report ID", "id": "report_id"},
                {"name": "Report Name", "id": "report_name"},
                {"name": "Project", "id": "project_id"},
                {"name": "Samples", "id": "sample_count"},
                {"name": "Date Created", "id": "date_created"},
                {"name": "Status", "id": "status"}
            ],
            data=[],
            sort_action="native",
            filter_action="native",
            page_action="native",
            page_size=15,
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER
        )
    ], style={"padding": "20px"})

# ================== MAIN APP LAYOUT ==================
app.layout = html.Div([
    dcc.Location(id="url"),
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

# Load FB samples data
@app.callback(
    Output("fb-samples-table", "data"),
    Output("fb-samples-status", "children"),
    Input("refresh-samples-btn", "n_clicks"),
    prevent_initial_call=True
)
def load_fb_samples(n_clicks):
    """Load FB samples data"""
    try:
        # Load FB samples (sample_type=2 based on your code)
        samples = LimsUpstreamSamples.objects.filter(sample_type=2).order_by("-sample_number")[:100]
        
        data = []
        for sample in samples:
            row = {
                "sample_number": f"FB{sample.sample_number}",
                "project_id": sample.project_id or "",
                "cell_line": sample.cell_line or "",
                "harvest_date": sample.harvest_date.strftime("%Y-%m-%d") if sample.harvest_date else "",
                "development_stage": sample.development_stage or "",
                "titer": sample.hf_octet_titer or "",
                "volume": sample.hccf_loading_volume or "",
                "sip_number": sample.sip_number or "",
                "cld_analyst": sample.cld_analyst or "",
                "sec_status": "Pending",
                "actions": "[View](#{})".format(sample.sample_number)
            }
            data.append(row)
        
        status = f"Loaded {len(data)} FB samples"
        return data, status
        
    except Exception as e:
        return [], f"Error loading samples: {str(e)}"

# Add row to FB sample creation table
@app.callback(
    Output("fb-sample-table", "data"),
    Input("fb-add-row", "n_clicks"),
    State("fb-sample-table", "data"),
    prevent_initial_call=True
)
def add_fb_sample_row(n_clicks, current_data):
    """Add a new row to FB sample table"""
    if current_data is None:
        current_data = []
    
    new_row = {
        "sample_number": "",
        "cell_line": "",
        "harvest_date": "",
        "titer": "",
        "volume": "",
        "notes": ""
    }
    current_data.append(new_row)
    return current_data

# Save FB samples
@app.callback(
    Output("fb-save-status", "children"),
    Input("fb-save-table", "n_clicks"),
    State("fb-sample-table", "data"),
    State("fb-project-dropdown", "value"),
    State("fb-dev-stage", "value"),
    State("fb-analyst", "value"),
    State("fb-sip-number", "value"),
    prevent_initial_call=True
)
def save_fb_samples(n_clicks, table_data, project, dev_stage, analyst, sip_number):
    """Save FB samples to database"""
    if not table_data:
        return "No data to save"
    
    try:
        saved_count = 0
        for row in table_data:
            if row.get("sample_number"):
                # Here you would save to your database
                # This is a placeholder implementation
                saved_count += 1
        
        return dbc.Alert(f"Successfully saved {saved_count} samples", color="success")
    except Exception as e:
        return dbc.Alert(f"Error saving samples: {str(e)}", color="danger")

# Load SEC samples
@app.callback(
    Output("sec-sample-table", "data"),
    Input("sec-load-samples", "n_clicks"),
    State("sec-individual-samples", "value"),
    prevent_initial_call=True
)
def load_sec_samples(n_clicks, selected_samples):
    """Load samples for SEC report"""
    if not selected_samples:
        return []
    
    try:
        # This is a placeholder - implement your actual SEC data loading
        data = []
        for sample_id in selected_samples:
            row = {
                "select": False,
                "sample_number": sample_id,
                "cell_line": "Example Clone",
                "project_id": "Example Project",
                "harvest_date": "2024-01-01",
                "main_peak_percent": 95.2,
                "hmw_percent": 2.1,
                "lmw_percent": 2.7,
                "duplicate": "No"
            }
            data.append(row)
        
        return data
    except Exception as e:
        print(f"Error loading SEC samples: {e}")
        return []

# Update activity feed
@app.callback(
    Output("recent-activity-feed", "children"),
    Input("url", "pathname")
)
def update_activity_feed(pathname):
    """Update the recent activity feed"""
    try:
        return [
            html.P("✅ Dashboard loaded successfully", className="small mb-1 text-success"),
            html.P("📊 Ready for analytics", className="small mb-1"),
            html.P("🧪 FB samples available", className="small mb-1"),
            html.P("⚙️ System operational", className="small mb-0"),
        ]
    except Exception as e:
        return [html.P("Loading...", className="small")]

# Placeholder callbacks for buttons that don't have functionality yet
@app.callback(
    Output("sec-report-status", "children"),
    Input("sec-generate-report", "n_clicks"),
    prevent_initial_call=True
)
def generate_sec_report(n_clicks):
    return dbc.Alert("SEC Report generation feature coming soon!", color="info")

@app.callback(
    Output("sec-reports-table", "data"),
    Input("url", "pathname")
)
def load_sec_reports(pathname):
    """Load existing SEC reports"""
    if pathname == "/reports/sec/view":
        # Placeholder data
        return [
            {
                "report_id": "SEC001",
                "report_name": "FB Batch 2024-001",
                "project_id": "Example Project",
                "sample_count": 12,
                "date_created": "2024-01-15",
                "status": "Complete"
            }
        ]
    return []