# samples/layouts/sample_sets.py
"""
Sample sets layout with enhanced SEC integration
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from ...shared.styles.common_styles import (
    PAGE_CONTENT_STYLE, TABLE_STYLE_CELL, TABLE_STYLE_HEADER_LIGHT,
    SAMPLE_SET_COLUMNS, FB_SAMPLE_COLUMNS, ICONS, get_status_style_conditional
)


def create_sample_sets_layout():
    """Create the main sample sets layout with SEC integration"""
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3([
                    html.I(className=f"fas {ICONS['sample_sets']} me-2"),
                    "FB Sample Sets"
                ], className="text-primary mb-1"),
                html.P(
                    "Sample sets grouped by project, SIP, and development stage. Request SEC analysis or view existing results.",
                    className="text-muted mb-3"
                )
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className=f"fas {ICONS['refresh']} me-1"),
                        "Refresh"
                    ], id="refresh-sample-sets", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className=f"fas {ICONS['sec']} me-1"),
                        "SEC Dashboard"
                    ], href="/sec/dashboard", color="info", size="sm"),
                    dbc.Button([
                        html.I(className=f"fas {ICONS['samples']} me-1"),
                        "View All Samples"
                    ], href="/fb-samples/view", color="outline-secondary", size="sm")
                ])
            ], md=4, className="text-end")
        ], className="mb-3"),

        # Instructions Card
        create_instructions_card(),

        # Sample Sets Table
        dbc.Card([
            dbc.CardHeader([
                html.H5("📊 Sample Sets with SEC Status", className="mb-0")
            ]),
            dbc.CardBody([
                dash_table.DataTable(
                    id="enhanced-sample-sets-table",
                    columns=SAMPLE_SET_COLUMNS,
                    data=[],
                    filter_action="native",
                    sort_action="native",
                    page_action="native",
                    page_size=25,
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER_LIGHT,
                    style_data_conditional=get_status_style_conditional(),
                    markdown_options={"link_target": "_self"}
                )
            ])
        ], className="mb-4"),

        # Status and Actions
        html.Div(id="sample-sets-status", className="text-muted small mt-2"),

        # Hidden components for callbacks
        dcc.Store(id="sample-sets-data", data=[]),
        dcc.Store(id="selected-sample-set", data={})

    ], style=PAGE_CONTENT_STYLE)


def create_all_samples_layout():
    """Create layout for viewing all FB samples with SEC status"""
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3([
                    html.I(className=f"fas {ICONS['samples']} me-2"),
                    "All FB Samples"
                ], className="text-primary mb-1"),
                html.P("Complete list of Fed Batch samples with SEC analysis status",
                       className="text-muted mb-3")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className=f"fas {ICONS['refresh']} me-1"),
                        "Refresh"
                    ], id="refresh-all-samples", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className=f"fas {ICONS['save']} me-1"),
                        "Save Changes"
                    ], id="save-all-samples", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className=f"fas {ICONS['add']} me-1"),
                        "Add Samples"
                    ], href="/fb-samples/create", color="success", size="sm")
                ])
            ], md=4, className="text-end")
        ], className="mb-3"),

        # All Samples Table
        dbc.Card([
            dbc.CardHeader([
                html.H5("🧪 All FB Samples", className="mb-0")
            ]),
            dbc.CardBody([
                dash_table.DataTable(
                    id="all-fb-samples-table",
                    columns=FB_SAMPLE_COLUMNS,
                    data=[],
                    editable=True,
                    sort_action="native",
                    filter_action="native",
                    page_action="native",
                    page_size=50,
                    row_selectable="multi",
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER_LIGHT,
                    style_data_conditional=get_status_style_conditional(),
                    markdown_options={"link_target": "_blank"}
                )
            ])
        ], className="mb-4"),

        # Status
        html.Div(id="all-samples-status", className="text-muted small mt-2")

    ], style=PAGE_CONTENT_STYLE)


def create_create_samples_layout():
    """Create layout for adding new FB samples"""
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H3([
                    html.I(className=f"fas {ICONS['add']} me-2"),
                    "Create FB Samples"
                ], className="text-primary mb-1"),
                html.P("Add new Fed Batch samples to the system",
                       className="text-muted mb-3")
            ])
        ], className="mb-4"),

        # Form Section
        create_sample_form_section(),

        # Sample Creation Table
        create_sample_creation_table(),

        # Status and Actions
        html.Div(id="create-samples-status", className="mt-3")

    ], style=PAGE_CONTENT_STYLE)


def create_instructions_card():
    """Create instructions card for sample sets"""
    return dbc.Card([
        dbc.CardBody([
            html.H6("📋 How to use Sample Sets:", className="text-primary mb-2"),
            html.Ol([
                html.Li("Review sample sets grouped by project, SIP, and development stage"),
                html.Li("Check SEC Status column to see analysis progress"),
                html.Li("Click 'Request SEC Analysis' to create LIMS analysis records"),
                html.Li("Click 'View/Create SEC Report' to analyze samples"),
                html.Li("Completed analyses will show '✅ Complete' status")
            ], className="mb-0 small")
        ])
    ], className="mb-4")


def create_sample_form_section():
    """Create the sample creation form section"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("📝 Sample Information", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Project *"),
                    dcc.Dropdown(
                        id="create-project-dropdown",
                        placeholder="Select protein - molecule type",
                        style={"width": "100%"}
                    )
                ], md=4),
                dbc.Col([
                    dbc.Label("Vessel Type *"),
                    dcc.Dropdown(
                        id="create-vessel-type",
                        options=[
                            {"label": "SF", "value": "SF"},
                            {"label": "BRX", "value": "BRX"}
                        ],
                        value="SF",
                        style={"width": "100%"}
                    )
                ], md=2),
                dbc.Col([
                    dbc.Label("Development Stage *"),
                    dcc.Dropdown(
                        id="create-dev-stage",
                        options=[
                            {"label": "MP", "value": "MP"},
                            {"label": "pMP", "value": "pMP"},
                            {"label": "BP", "value": "BP"},
                            {"label": "BP SCC", "value": "BP SCC"},
                            {"label": "MP SCC", "value": "MP SCC"}
                        ],
                        value="MP",
                        style={"width": "100%"}
                    )
                ], md=2),
                dbc.Col([
                    dbc.Label("CLD Analyst *"),
                    dcc.Dropdown(
                        id="create-analyst",
                        options=[
                            {"label": "YY", "value": "YY"},
                            {"label": "JS", "value": "JS"},
                            {"label": "YW", "value": "YW"}
                        ],
                        placeholder="Select analyst",
                        style={"width": "100%"}
                    )
                ], md=2),
                dbc.Col([
                    dbc.Label("SIP #"),
                    dcc.Input(
                        id="create-sip-number",
                        type="number",
                        placeholder="SIP#",
                        style={"width": "100%"}
                    )
                ], md=2)
            ], className="g-3")
        ])
    ], className="mb-4")


def create_sample_creation_table():
    """Create the sample creation table section"""
    return html.Div([
        # Table Controls
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className=f"fas {ICONS['add']} me-1"),
                        "Add Row"
                    ], id="add-sample-row", color="secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-trash me-1"),
                        "Clear Table"
                    ], id="clear-sample-table", color="danger", size="sm"),
                    dbc.Button([
                        html.I(className=f"fas {ICONS['save']} me-1"),
                        "Save Samples"
                    ], id="save-new-samples", color="primary", size="sm")
                ])
            ], md=6),
            dbc.Col([
                html.Div(id="sample-creation-status", className="text-end small")
            ], md=6)
        ], className="mb-3"),

        # Sample Table
        dbc.Card([
            dbc.CardHeader([
                html.H5("📋 Sample Details", className="mb-0")
            ]),
            dbc.CardBody([
                dash_table.DataTable(
                    id="create-samples-table",
                    columns=[
                        {"name": "Sample Number", "id": "sample_number", "editable": False},
                        {"name": "Clone", "id": "cell_line", "editable": True},
                        {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
                        {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
                        {"name": "ProAqa HF", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
                        {"name": "ProAqa E", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
                        {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
                        {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
                        {"name": "Eluate Volume", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
                        {"name": "Note", "id": "note", "editable": True}
                    ],
                    data=[],
                    editable=True,
                    row_deletable=True,
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER_LIGHT
                )
            ])
        ])
    ])


def create_sec_request_confirmation_modal():
    """Create modal for SEC analysis request confirmation"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className=f"fas {ICONS['sec']} me-2"),
                "Request SEC Analysis"
            ])
        ]),
        dbc.ModalBody([
            html.Div(id="sec-request-modal-content")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="sec-request-cancel", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-microscope me-2"),
                "Confirm Request"
            ], id="sec-request-confirm", color="primary")
        ])
    ], id="sec-request-modal", is_open=False, size="lg")


def create_sample_details_modal():
    """Create modal for viewing sample details"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4("Sample Set Details")
        ]),
        dbc.ModalBody([
            html.Div(id="sample-details-modal-content")
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-sample-details", color="secondary")
        ])
    ], id="sample-details-modal", is_open=False, size="xl")


def create_bulk_actions_section():
    """Create bulk actions section for sample sets"""
    return dbc.Card([
        dbc.CardHeader([
            html.H6("🔧 Bulk Actions", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-microscope me-2"),
                        "Request SEC for All Pending"
                    ], id="bulk-sec-request", color="info", size="sm", disabled=True)
                ], md=6),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-chart-line me-2"),
                        "Generate Combined Report"
                    ], id="bulk-report-generate", color="success", size="sm", disabled=True)
                ], md=6)
            ]),
            html.Div(id="bulk-actions-status", className="mt-2 small")
        ])
    ], className="mt-3")