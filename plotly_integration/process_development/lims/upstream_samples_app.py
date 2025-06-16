import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context, exceptions
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from django.db import IntegrityError
from django_plotly_dash import DjangoDash
from django.db.models import Max

from plotly_integration.models import LimsProjectInformation, LimsUpstreamSamples, LimsSampleAnalysis

app = DjangoDash("UPSampleManagementApp", external_stylesheets=[dbc.themes.BOOTSTRAP], title="UP Sample Manager")

TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "2px 4px",
    "fontSize": "11px",
    "border": "1px solid #ddd",
    "minWidth": "100px",
    "width": "100px",
    "maxWidth": "200px",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#006699",
    "fontWeight": "bold",
    "color": "white",
    "textAlign": "center",
    "fontSize": "11px",
    "padding": "2px 4px"
}

UP_SAMPLE_FIELDS = [
    {"name": "Project", "id": "project", "editable": False},
    {"name": "Experiment #", "id": "experiment_number", "editable": True},
    {"name": "Sample #", "id": "sample_number", "editable": False},
    {"name": "Day", "id": "culture_duration", "editable": True},
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "Vessel Type", "id": "vessel_type", "editable": True},
    # {"name": "SIP #", "id": "sip_number", "editable": True},
    # {"name": "Description", "id": "description", "editable": True},
    # {"name": "Analyst", "id": "analyst", "editable": True},
    {"name": "Harvest Date (YYYY-MM-DD)", "id": "harvest_date", "editable": True, "type": "datetime"},
    # {"name": "Unifi #", "id": "unifi_number", "editable": True},
    # {"name": "Titer Comment", "id": "titer_comment", "editable": True},
    # {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa Eluate Titer", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
    {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
    {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
    {"name": "Eluate Volume", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
    # {"name": "ProA Recovery", "id": "proa_recovery", "editable": True, "type": "numeric"},
    {"name": "ProAqa Recovery", "id": "fast_pro_a_recovery", "editable": False, "type": "numeric"},
    {"name": "A280 Recovery", "id": "purification_recovery_a280", "editable": False, "type": "numeric"},
    # {"name": "Column Size", "id": "proa_column_size", "editable": True, "type": "numeric"},
    # {"name": "Column ID", "id": "column_id", "editable": True},
    {"name": "Note", "id": "note", "editable": True},
]

FIELD_IDS = [f["id"] for f in UP_SAMPLE_FIELDS]
EDITABLE_FIELDS = [f["id"] for f in UP_SAMPLE_FIELDS if f["editable"] and f["id"] != "sample_number"]

app.layout = html.Div([
    html.Div([
        html.H2("UP Sample Management", style={"margin": "10px 0", "color": "#006699"}),
        html.Hr(style={"marginBottom": "10px"})
    ]),
    dcc.Store(id="upstream-context", data={"mode": "", "sample_type": 2}),
    dcc.Tabs(id="upstream-tabs", value="view-tab", children=[

        # View Samples Tab
        dcc.Tab(label="View Samples", value="view-tab", children=[
            html.Div([
                dbc.Row([
                    dbc.Col(
                        dbc.Button("💾 Update and Refresh Table", id="update-up-view-btn", color="primary", size="sm"),
                        width="auto"),
                    dbc.Col(html.Div(id="update-up-view-status", style={"fontSize": "11px", "marginTop": "5px"}))
                ], className="mb-2 g-2"),

                dash_table.DataTable(
                    id="view-sample-table",
                    columns=[
                        {
                            "name": col["name"],
                            "id": col["id"],
                            "editable": col["editable"],
                            "type": col.get("type", "text")
                        } for col in UP_SAMPLE_FIELDS
                    ],
                    data=[],
                    editable=True,
                    sort_action="native",
                    filter_action="native",
                    page_action="native",
                    page_size=25,
                    row_deletable=False,
                    # fixed_columns={"headers": True, "data": 4},
                    # fixed_rows={"headers": True},
                    # style_table={"height": "100vh", "overflowY": "auto"},
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER,
                    style_data_conditional=[
                        {
                            "if": {"column_id": col["id"]},
                            "backgroundColor": "#f0f0f0",  # light gray
                            "color": "black"
                        }
                        for col in UP_SAMPLE_FIELDS if not col["editable"]
                    ],
                )
            ], style={"padding": "10px"})
        ]),

        # Create Samples Tab
        dcc.Tab(label="Create Samples", value="create-tab", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Project:"),
                        dcc.Dropdown(
                            id="up-project-dropdown",
                            placeholder="Select protein - molecule type",
                            style={"width": "100%"}
                        )
                    ], width=4),

                    dbc.Col([
                        dbc.Label("Vessel Type:"),
                        dcc.Dropdown(
                            id="up-vessel-type",
                            options=[{"label": "SF", "value": "SF"}, {"label": "BRX", "value": "BRX"}],
                            value="BRX",
                            placeholder="Select category",
                            style={"width": "100%"}
                        )
                    ], width=2),

                    dbc.Col([
                        dbc.Label("Experiment #:"),
                        dcc.Input(id="up-experiment-number", type="number",
                                  placeholder="Experiment number", style={"width": "100%"})
                    ], width=2)
                ], className="mb-4 g-2"),

                dbc.Row([
                    dbc.Col(dbc.Button("➕ Add Row", id="add-up-row", color="secondary", size="sm"), width="auto"),
                    dbc.Col(dbc.Button("🧹 Clear Table", id="clear-up-table", color="danger", size="sm"),
                            width="auto"),
                    dbc.Col(
                        dbc.Button("💾 Save UP Samples", id="save-up-table", color="primary", size="sm", n_clicks=0),
                        width="auto"),
                    dbc.Col(html.Div(id="save-up-status", style={"fontSize": "11px", "marginTop": "5px"}))
                ], className="mb-2 g-2"),

                dash_table.DataTable(
                    id="up-sample-table",
                    columns=[
                        {"name": "Sample Number", "id": "sample_number", "editable": False},
                        {"name": "ID", "id": "id", "editable": True},
                        {"name": "Clone", "id": "clone", "editable": True},
                        {"name": "Day", "id": "culture_duration", "editable": True},
                        {"name": "Description", "id": "description", "editable": True},
                        {"name": "Harvest Date (YYYY-MM-DD)", "id": "harvest_date", "editable": True,
                         "type": "datetime"},
                        {"name": "Note", "id": "note", "editable": True}
                    ],
                    data=[],
                    editable=True,
                    row_deletable=True,
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER,
                    style_table={"overflowX": "auto"}
                )
            ], style={"padding": "10px"})
        ])
    ])
])


def calculate_recoveries(sample):
    fast_pro_a_recovery = None
    a280_recovery = None

    try:
        if sample.proa_eluate_volume and sample.pro_aqa_e_titer and sample.hccf_loading_volume and sample.pro_aqa_hf_titer:
            fast_pro_a_recovery = (
                                          sample.proa_eluate_volume * sample.pro_aqa_e_titer
                                  ) / (
                                          sample.hccf_loading_volume * sample.pro_aqa_hf_titer
                                  ) * 100

        if sample.proa_eluate_volume and sample.proa_eluate_a280_conc and sample.hccf_loading_volume and sample.proa_eluate_a280_conc:
            a280_recovery = (
                                    sample.proa_eluate_volume * sample.proa_eluate_a280_conc
                            ) / (
                                    sample.hccf_loading_volume * sample.pro_aqa_hf_titer
                            ) * 100  # If you're comparing to a different input A280, update accordingly
    except ZeroDivisionError:
        pass

    return round(fast_pro_a_recovery, 1) if fast_pro_a_recovery is not None else None, \
        round(a280_recovery, 1) if a280_recovery is not None else None


# View Samples Table
@app.callback(
    Output("view-sample-table", "data"),
    Output("update-up-view-status", "children"),
    Input("upstream-tabs", "value"),
    Input("update-up-view-btn", "n_clicks"),
    State("view-sample-table", "data"),
    prevent_initial_call=False
)
def load_or_update_view_samples(tab, n_clicks, table_data):
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    updated, errors = 0, 0

    # Only update if the button was clicked
    if triggered == "update-up-view-btn" and table_data:
        for row in table_data:
            try:
                update_data = {field: row.get(field) or None for field in EDITABLE_FIELDS}
                LimsUpstreamSamples.objects.filter(
                    sample_number=row["sample_number"], sample_type=1
                ).update(**update_data)
                updated += 1
            except Exception as e:
                print(f"Update failed for sample {row.get('sample_number')}: {e}")
                errors += 1

    # Always reload data
    samples = LimsUpstreamSamples.objects.filter(sample_type=1)
    new_data = []
    for s in samples:
        fast_pro_a, a280 = calculate_recoveries(s)
        row = {
            field: getattr(s, field) if field != "harvest_date" or not getattr(s, field)
            else getattr(s, field).strftime("%Y-%m-%d")
            for field in FIELD_IDS
        }
        row["fast_pro_a_recovery"] = fast_pro_a
        row["purification_recovery_a280"] = a280
        new_data.append(row)

    status_msg = f"✅ Updated: {updated} | ❌ Errors: {errors}" if triggered == "update-up-view-btn" else dash.no_update
    return new_data, status_msg


# Sample Creation
@app.callback(
    Output("up-project-dropdown", "options"),
    Input("upstream-tabs", "value"),
    prevent_initial_call=False
)
def populate_project_dropdown(tab):
    if tab != "create-tab":
        raise dash.exceptions.PreventUpdate

    project_qs = LimsProjectInformation.objects.all().order_by("protein", "molecule_type")

    options = [
        {
            "label": f"{p.protein} - {p.molecule_type}",
            "value": f"{p.protein}"
        }
        for p in project_qs if p.protein and p.molecule_type
    ]

    return options


@app.callback(
    Output("up-sample-table", "data"),
    Input("add-up-row", "n_clicks_timestamp"),
    Input("clear-up-table", "n_clicks_timestamp"),
    State("up-sample-table", "data"),
    prevent_initial_call=True
)
def modify_up_sample_table(add_ts, clear_ts, current_data):
    from plotly_integration.models import LimsUpstreamSamples
    from django.db.models import Max

    if current_data is None:
        current_data = []

    timestamps = {
        "add": add_ts or 0,
        "clear": clear_ts or 0,
    }
    latest_action = max(timestamps, key=timestamps.get)

    if latest_action == "clear":
        return []

    if latest_action == "add":
        db_max = LimsUpstreamSamples.objects.filter(sample_type=1).aggregate(Max("sample_number"))
        max_sample_number = db_max["sample_number__max"] or 0

        # check in-memory data
        current_numbers = [
            int(row["sample_number"]) for row in current_data
            if str(row.get("sample_number")).isdigit()
        ]
        if current_numbers:
            max_sample_number = max(max_sample_number, max(current_numbers))

        next_sample_number = max_sample_number + 1
        current_data.append({
            "sample_number": next_sample_number,
            "id": "",
            "clone": "",
            "culture_duration": "",
            "description": "",
            "harvest_date": "",
            "note": ""
        })

        return current_data

    raise PreventUpdate


@app.callback(
    Output("save-up-status", "children"),
    Input("save-up-table", "n_clicks_timestamp"),
    State("up-sample-table", "data"),
    State("up-project-dropdown", "value"),
    State("up-vessel-type", "value"),
    State("up-experiment-number", "value"),
    prevent_initial_call=True
)
def save_up_samples(save_up_ts, table_data, project, vessel_type, experiment_number):
    timestamps = {
        "save_up": save_up_ts or 0,
    }
    latest_action = max(timestamps, key=timestamps.get)

    if latest_action != "save_up":
        raise exceptions.PreventUpdate

    if not table_data:
        return "❌ No data to save."
    if not project or not vessel_type:
        return "⚠️ Please fill in Project, Vessel Type."

    print(f"💾 Saving UP samples for project '{project}' | vessel: {vessel_type} | exp: {experiment_number}")

    created, skipped, errors = 0, 0, 0

    for row in table_data:
        try:
            if not row.get("sample_number"):
                skipped += 1
                continue

            # Create or update the LimsUpstreamSamples object
            upstream_sample, created_flag = LimsUpstreamSamples.objects.update_or_create(
                sample_number=row["sample_number"],
                sample_type=1,  # Ensure this is set to UP
                defaults={
                    "project": project,
                    "vessel_type": vessel_type,
                    "experiment_number": experiment_number,
                    "sip_number": row.get("id", ""),
                    "cell_line": row.get("clone", ""),
                    "culture_duration": row.get("culture_duration") or None,
                    "description": row.get("description", ""),
                    "harvest_date": row.get("harvest_date") or None,
                    "note": row.get("note", "")
                }
            )

            # Now, create or update the LimsSampleAnalysis with the FK link to the upstream sample
            LimsSampleAnalysis.objects.update_or_create(
                sample_id=f'UP{row["sample_number"]}',
                sample_type=1,
                defaults={
                    "sample_date": row.get("harvest_date") or None,
                    "project_id": project,
                    "description": row.get("description", ""),
                    "notes": row.get("note", ""),
                    "dn": None,
                    "a280_result": None,
                    "up": upstream_sample.id  # Link to the LimsUpstreamSamples by its ID
                }
            )

            created += 1 if created_flag else 0

        except Exception as e:
            print(f"❌ Error saving sample {row.get('sample_number')}: {e}")
            errors += 1

    return f"✅ Created/Updated: {created} | Skipped: {skipped} | Errors: {errors}"