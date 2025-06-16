from dash import html, dcc, dash_table

from plotly_integration.process_development.downstream_processing.empower.sec_report_app.layout.layout import app_layout
from .table_config import UP_SAMPLE_FIELDS, TABLE_STYLE_CELL, TABLE_STYLE_HEADER, SEC_COLUMNS
import dash_bootstrap_components as dbc

# Layout for the Dash app
# app_layout = html.Div([
#     html.Div([
#         html.H2("CLD Sample Management", style={"margin": "10px 0", "color": "#006699"}),
#         html.Hr(style={"marginBottom": "10px"})
#     ]),
#
#     dcc.Store(id="upstream-context", data={"mode": "", "sample_type": 1}),
#     dcc.Tabs(id="upstream-tabs", value="sample-sets-tab", children=[
#
#         dcc.Tab(label="View Sample Sets", value="sample-sets-tab", children=[
#             dcc.Store(id="selected-sample-set-fbs", data=[]),
#             dcc.Tabs(id="sample-set-subtabs", value="sample-set-table-tab", children=[
#
#                 # Subtab 1: Sample Set Table
#                 dcc.Tab(label="Sample Set Table", value="sample-set-table-tab", children=[
#                     html.Div([
#                         html.H5("FB Sample Sets", style={"marginTop": "10px"}),
#
#                         dash_table.DataTable(
#                             id="sample-set-table",
#                             columns=[
#                                 {"name": "Project", "id": "project"},
#                                 {"name": "Sample Range", "id": "range"},
#                                 {"name": "SIP #", "id": "sip"},
#                                 {"name": "Development Stage", "id": "development_stage"},
#                                 {"name": "Number Samples", "id": "count"},
#                                 {"name": "View SEC", "id": "view_sec_link", "presentation": "markdown"},
#                                 {"name": "View SEC", "id": "view_sec", "presentation": "markdown"}
#                             ],
#                             data=[],
#                             filter_action="native",
#                             sort_action="native",
#                             # row_selectable="single",
#                             style_cell=TABLE_STYLE_CELL,
#                             style_header=TABLE_STYLE_HEADER,
#                             style_data_conditional=[
#                                 {
#                                     "if": {
#                                         "column_id": "view_sec_link",
#                                         "filter_query": '{view_sec_link} contains "⚠️"'
#                                     },
#                                     "color": "red",
#                                     "fontWeight": "bold"
#                                 }
#                             ],
#                             markdown_options={"view_sec_link": "_blank", "view_sec": "_blank"},
#                             style_table={"marginTop": "10px"}
#                         ),
#                         html.Div(id="sample-set-table-status", style={"fontSize": "11px", "marginTop": "5px"}),
#                         html.Div(id="report-update-status",
#                                  style={"fontSize": "11px", "marginTop": "5px", "color": "#006699"})
#                     ], style={"padding": "10px"})
#                 ]),
#
#                 # Subtab 2: View Samples in Set
#                 dcc.Tab(label="View Samples", value="sample-set-view-samples-tab", children=[
#                     html.Div([
#                         dash_table.DataTable(
#                             id="sample-set-sample-table",
#                             columns=[
#                                 {
#                                     "name": col["name"],
#                                     "id": col["id"],
#                                     "editable": col["editable"],
#                                     "type": col.get("type", "text"),
#                                     **({"presentation": col["presentation"]} if "presentation" in col else {})
#                                 } for col in UP_SAMPLE_FIELDS
#                             ],
#                             data=[],
#                             editable=False,
#                             sort_action="native",
#                             filter_action="native",
#                             page_action="native",
#                             page_size=25,
#                             row_deletable=False,
#                             markdown_options={"link_target": "_blank"},
#                             style_cell=TABLE_STYLE_CELL,
#                             style_header=TABLE_STYLE_HEADER,
#                             style_data_conditional=[
#                                 {
#                                     "if": {"column_id": col["id"]},
#                                     "backgroundColor": "#f0f0f0",
#                                     "color": "black"
#                                 } for col in UP_SAMPLE_FIELDS if not col["editable"]
#                             ],
#                         )
#                     ], style={"padding": "10px"})
#                 ]),
#
#                 # Subtab 3: SEC Report Creation
#                 dcc.Tab(
#                     label="SEC Report Creation",
#                     value="sample-set-sec-report-tab",
#                     children=[
#                         html.Div([
#                             html.H5("Create/Edit SEC Report", style={"marginTop": "10px", "color": "#0047b3"}),
#
#                             # Status blocks
#                             dbc.Row([
#                                 dbc.Col(html.Div(id="sec-expected-status", style={"fontSize": "12px", "color": "#555"}),
#                                         width=6),
#                                 dbc.Col(html.Div(id="sec-report-metadata",
#                                                  style={"fontSize": "12px", "color": "#0047b3", "textAlign": "right"}),
#                                         width=6)
#                             ], className="mb-2"),
#
#                             # Sample table
#                             dbc.Row([
#                                 dbc.Col([
#                                     dash_table.DataTable(
#                                         id="sec-report-sample-table",
#                                         columns=SEC_COLUMNS,
#                                         data=[],
#                                         row_selectable="multi",
#                                         filter_action="native",
#                                         sort_action="native",
#                                         style_table={"overflowX": "auto"},
#                                         style_cell=TABLE_STYLE_CELL,
#                                         style_header=TABLE_STYLE_HEADER,
#                                         style_data={"backgroundColor": "white", "color": "#333"},
#                                         markdown_options={"link_target": "_blank"},
#                                         style_data_conditional=[{
#                                             "if": {"filter_query": "{duplicate} eq true"},
#                                             "backgroundColor": "#fff9c4"  # light yellow
#                                         }]
#                                     )
#                                 ])
#                             ]),
#
#                             # Buttons
#                             dbc.Row([
#                                 dbc.Col([
#                                     dbc.Button("Update/Save", id="submit-sec-report", color="primary", className="mt-3")
#                                 ]),
#                                 dbc.Col([
#                                     dbc.Button("🔬 View Report", id="view-sec-report", color="secondary",
#                                                className="mt-3"),
#                                     dcc.Location(id="sec-report-redirect", refresh=True)
#                                 ]),
#                                 dbc.Col(html.Div(id="sec-report-status", className="mt-3"), width=12)
#                             ]),
#                         ], style={"padding": "15px"})
#                     ]
#                 )
#             ])
#         ]),
#         # View Samples Tab
#         dcc.Tab(label="View Samples", value="view-samples", children=[
#             html.Div([
#                 dcc.Location(id="sec-redirect", refresh=True),
#                 dbc.Row([
#                     dbc.Col(
#                         dbc.Button("💾 Update and Refresh Table", id="update-up-view-btn", color="primary", size="sm"),
#                         width="auto"),
#                     dbc.Col(html.Div(id="update-up-view-status", style={"fontSize": "11px", "marginTop": "5px"}))
#                 ], className="mb-2 g-2"),
#
#                 dash_table.DataTable(
#                     id="view-sample-table",
#                     columns=[
#                         {
#                             "name": col["name"],
#                             "id": col["id"],
#                             "editable": col["editable"],
#                             "type": col.get("type", "text"),
#                             **({("presentation"): col["presentation"]} if "presentation" in col else {})
#                         } for col in UP_SAMPLE_FIELDS
#                     ],
#                     data=[],
#                     editable=True,
#                     sort_action="native",
#                     filter_action="native",
#                     page_action="native",
#                     page_size=25,
#                     row_deletable=False,
#                     markdown_options={"link_target": "_blank"},  # Add this line
#                     style_cell=TABLE_STYLE_CELL,
#                     style_header=TABLE_STYLE_HEADER,
#                     style_data_conditional=[
#                         {
#                             "if": {"column_id": col["id"]},
#                             "backgroundColor": "#f0f0f0",
#                             "color": "black"
#                         } for col in UP_SAMPLE_FIELDS if not col["editable"]
#                     ],
#                 )], style={"padding": "10px"})
#         ]),
#
#         # Create Samples Tab
#         dcc.Tab(label="Create Samples", value="create-tab", children=[
#             html.Div([
#                 dbc.Row([
#                     dbc.Col([
#                         dbc.Label("Project:"),
#                         dcc.Dropdown(
#                             id="up-project-dropdown",
#                             placeholder="Select protein - molecule type",
#                             style={"width": "100%"}
#                         )
#                     ], width=4),
#
#                     dbc.Col([
#                         dbc.Label("Vessel Type:"),
#                         dcc.Dropdown(
#                             id="up-vessel-type",
#                             options=[{"label": "SF", "value": "SF"}, {"label": "BRX", "value": "BRX"}],
#                             value="SF",
#                             placeholder="Select category",
#                             style={"width": "100%"}
#                         )
#                     ], width=2),
#
#                     dbc.Col([
#                         dbc.Label("Development Stage:"),
#                         dcc.Dropdown(
#                             id="cld-dev-stage",
#                             options=[
#                                 {"label": "MP", "value": "MP"},
#                                 {"label": "pMP", "value": "pMP"},
#                                 {"label": "BP", "value": "BP"},
#                                 {"label": "BP SCC", "value": "BP SCC"},
#                                 {"label": "MP SCC", "value": "MP SCC"},
#                             ],
#                             value="MP",
#                             placeholder="Select category",
#                             style={"width": "100%"}
#                         )
#                     ], width=2),
#
#                     dbc.Col([
#                         dbc.Label("CLD Analyst"),
#                         dcc.Dropdown(
#                             id="cld-analyst",
#                             options=[
#                                 {"label": "YY", "value": "YY"},
#                                 {"label": "JS", "value": "JS"},
#                                 {"label": "YW", "value": "YW"},
#                             ],
#
#                             placeholder="Select category",
#                             style={"width": "100%"}
#                         )
#                     ], width=2),
#
#                 ], className="mb-4 g-2"),
#
#                 dbc.Row([
#                     dbc.Col([
#                         dbc.Label("SIP#:"),
#                         dcc.Input(id="sip-number", type="number",
#                                   placeholder="SIP#", style={"width": "100%"})
#                     ], width=2),
#                     dbc.Col([
#                         dbc.Label("UNIFI#:"),
#                         dcc.Input(id="unifi-number", type="number",
#                                   placeholder="UNIFI#", style={"width": "100%"})
#                     ], width=2),
#                 ], className="mb-4 g-2"),
#
#                 dbc.Row([
#                     dbc.Col(dbc.Button("➕ Add Row", id="add-up-row", color="secondary", size="sm"), width="auto"),
#                     dbc.Col(dbc.Button("🧹 Clear Table", id="clear-up-table", color="danger", size="sm"),
#                             width="auto"),
#                     dbc.Col(
#                         dbc.Button("💾 Save UP Samples", id="save-up-table", color="primary", size="sm", n_clicks=0),
#                         width="auto"),
#                     dbc.Col(html.Div(id="save-up-status", style={"fontSize": "11px", "marginTop": "5px"}))
#                 ], className="mb-2 g-2"),
#
#                 dash_table.DataTable(
#                     id="up-sample-table",
#                     columns=[
#                         {"name": "Sample Number", "id": "sample_number", "editable": True},
#                         {"name": "Clone", "id": "cell_line", "editable": True},
#                         {"name": "Harvest Date (YYYY-MM-DD)", "id": "harvest_date", "editable": True,
#                          "type": "datetime"},
#                         {"name": "Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
#                         {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
#                         {"name": "ProAqa Eluate Titer", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
#                         {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
#                         {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
#                         {"name": "Eluate Volume", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
#                         {"name": "Fast ProAaq Recovery", "id": "fast_pro_a_recovery", "editable": False,
#                          "type": "numeric"},
#                         {"name": "A280 Recovery", "id": "purification_recovery_a280", "editable": False,
#                          "type": "numeric"},
#                         {"name": "Note", "id": "note", "editable": True}
#                     ],
#                     data=[],
#                     editable=True,
#                     row_deletable=True,
#                     style_cell=TABLE_STYLE_CELL,
#                     style_header=TABLE_STYLE_HEADER,
#                     style_table={"overflowX": "auto"}
#                 )
#             ], style={"padding": "10px"})
#         ])
#     ])
# ])


# Styles
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
}

CONTENT_STYLE = {
    "marginLeft": "260px",
    "marginRight": "20px",
    "padding": "20px",
}

# Sidebar
sidebar = html.Div([
    html.H3("📁 CLD Dashboard", className="display-6"),
    html.Hr(),
    dbc.Nav([
        dbc.NavLink("📁 Sample Sets - Table", href="/sample-sets/table", active="exact"),
        dbc.NavLink("📁 Sample Sets - View Samples", href="/sample-sets/view", active="exact"),
        dbc.NavLink("📁 Sample Sets - SEC Report", href="/sample-sets/sec", active="exact"),
        dbc.NavLink("🧪 View Samples", href="/view-samples", active="exact"),
        dbc.NavLink("➕ Create Samples", href="/create-samples", active="exact"),
    ], vertical=True, pills=True),
], style=SIDEBAR_STYLE)

# Placeholder for page content
content = html.Div(id="page-content", style=CONTENT_STYLE)

# Main layout
app_layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content
])

# Page contents
def sample_set_table_layout():
    return html.Div([
        html.H4("FB Sample Sets"),
        dash_table.DataTable(
            id="sample-set-table",
            columns=[
                {"name": "Project", "id": "project"},
                {"name": "Sample Range", "id": "range"},
                {"name": "SIP #", "id": "sip"},
                {"name": "Development Stage", "id": "development_stage"},
                {"name": "Number Samples", "id": "count"},
                {"name": "View SEC", "id": "view_sec_link", "presentation": "markdown"},
                {"name": "View SEC", "id": "view_sec", "presentation": "markdown"}
            ],
            data=[],
            filter_action="native",
            sort_action="native",
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER,
            style_table={"marginTop": "10px"}
        )
    ])

def sample_set_view_samples_layout():
    return html.Div([
        html.H4("Samples in Set"),
        dash_table.DataTable(
            id="sample-set-sample-table",
            columns=[
                {
                    "name": col["name"],
                    "id": col["id"],
                    "editable": col["editable"],
                    "type": col.get("type", "text"),
                    **({"presentation": col["presentation"]} if "presentation" in col else {})
                } for col in UP_SAMPLE_FIELDS
            ],
            data=[],
            editable=False,
            sort_action="native",
            filter_action="native",
            page_action="native",
            page_size=25,
            row_deletable=False,
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER
        )
    ])

def sample_set_sec_report_layout():
    return html.Div([
        html.H4("Create/Edit SEC Report"),
        dash_table.DataTable(
            id="sec-report-sample-table",
            columns=SEC_COLUMNS,
            data=[],
            row_selectable="multi",
            filter_action="native",
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER,
            style_data={"backgroundColor": "white", "color": "#333"}
        ),
        dbc.Row([
            dbc.Col(dbc.Button("Update/Save", id="submit-sec-report", color="primary", className="mt-3")),
            dbc.Col(dbc.Button("🔬 View Report", id="view-sec-report", color="secondary", className="mt-3")),
            dbc.Col(html.Div(id="sec-report-status", className="mt-3"), width=12)
        ])
    ])

def view_samples_layout():
    return html.Div([
        html.H4("View UP Samples"),
        dash_table.DataTable(
            id="view-sample-table",
            columns=[
                {
                    "name": col["name"],
                    "id": col["id"],
                    "editable": col["editable"],
                    "type": col.get("type", "text"),
                    **({"presentation": col["presentation"]} if "presentation" in col else {})
                } for col in UP_SAMPLE_FIELDS
            ],
            data=[],
            editable=True,
            sort_action="native",
            filter_action="native",
            page_action="native",
            page_size=25,
            row_deletable=False,
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER
        )
    ])

def create_samples_layout():
    return html.Div([
        html.H4("Create New UP Samples"),
        dbc.Row([
            dbc.Col(dbc.Button("➕ Add Row", id="add-up-row", color="secondary", size="sm")),
            dbc.Col(dbc.Button("💾 Save UP Samples", id="save-up-table", color="primary", size="sm"))
        ], className="mb-2 g-2"),

        dash_table.DataTable(
            id="up-sample-table",
            columns=[
                {"name": "Sample Number", "id": "sample_number", "editable": True},
                {"name": "Clone", "id": "cell_line", "editable": True},
                {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
                {"name": "Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
                {"name": "Note", "id": "note", "editable": True}
            ],
            data=[],
            editable=True,
            row_deletable=True,
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER
        )
    ])