import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context, exceptions
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from django.db import IntegrityError
from django_plotly_dash import DjangoDash
from django.db.models import Max

from plotly_integration.models import LimsProjectInformation, LimsUpstreamSamples, LimsSampleAnalysis

app = DjangoDash("CLDSampleManagementApp", external_stylesheets=[dbc.themes.BOOTSTRAP], title="CLD Sample Manager")

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
    # {"name": "Experiment #", "id": "experiment_number", "editable": True},
    {"name": "Sample #", "id": "sample_number", "editable": False},
    # {"name": "Day", "id": "culture_duration", "editable": True},
    {"name": "Clone", "id": "cell_line", "editable": True},
    # {"name": "Vessel Type", "id": "vessel_type", "editable": True},
    {"name": "SIP #", "id": "sip_number", "editable": True},
    {"name": "Development Stage", "id": "development_stage", "editable": True},
    {"name": "Analyst", "id": "analyst", "editable": True},
    {"name": "Harvest Date (YYYY-MM-DD)", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Unifi #", "id": "unifi_number", "editable": True},
    # {"name": "Titer Comment", "id": "titer_comment", "editable": True},
    {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
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
    {"name": "Report Link", "id": "report_link", "editable": False, "presentation": "markdown"}

]

FIELD_IDS = [f["id"] for f in UP_SAMPLE_FIELDS]
EDITABLE_FIELDS = [f["id"] for f in UP_SAMPLE_FIELDS if
                   f["editable"] and f["id"] not in ("sample_number", "report_link")]
NON_EDITABLE_FIELDS = [f["id"] for f in UP_SAMPLE_FIELDS if not f["editable"]]

app.layout = html.Div([
    html.Div([
        html.H2("CLD Sample Management", style={"margin": "10px 0", "color": "#006699"}),
        html.Hr(style={"marginBottom": "10px"})
    ]),

    dcc.Store(id="upstream-context", data={"mode": "", "sample_type": 1}),
    dcc.Tabs(id="upstream-tabs", value="sample-sets-tab", children=[

        dcc.Tab(label="View Sample Sets", value="sample-sets-tab", children=[
            html.Div([
                html.H5("FB Sample Sets", style={"marginTop": "10px"}),

                dash_table.DataTable(
                    id="sample-set-table",
                    columns=[
                        {"name": "Project", "id": "project"},
                        {"name": "Sample Range", "id": "range"},
                        {"name": "SIP #", "id": "sip"},
                        {"name": "Development Stage", "id": "development_stage"},
                        {"name": "Number Samples", "id": "count"},
                        {"name": "View SEC", "id": "view_sec_link", "presentation": "markdown"},
                        {
                            "name": "View SEC",
                            "id": "view_sec",
                            "presentation": "markdown"
                        }
                    ],
                    data=[],
                    row_selectable="single",
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER,
                    style_data_conditional=[
                        {
                            "if": {
                                "column_id": "view_sec_link",
                                "filter_query": '{view_sec_link} contains "⚠️"'
                            },
                            "color": "red",
                            "fontWeight": "bold"
                        }
                    ],

                    markdown_options={"view_sec_link": "_blank","view_sec": "_blank"},
                    style_table={"marginTop": "10px"}
                ),
                html.Div(id="sample-set-table-status", style={"fontSize": "11px", "marginTop": "5px"}),
                html.Div(id="report-update-status", style={"fontSize": "11px", "marginTop": "5px", "color": "#006699"})
            ], style={"padding": "10px"})
        ]),
        # View Samples Tab
        dcc.Tab(label="View Samples", value="view-samples", children=[
            html.Div([
                dcc.Location(id="sec-redirect", refresh=True),
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
                            "type": col.get("type", "text"),
                            **({("presentation"): col["presentation"]} if "presentation" in col else {})
                        } for col in UP_SAMPLE_FIELDS
                    ],
                    data=[],
                    editable=True,
                    sort_action="native",
                    filter_action="native",
                    page_action="native",
                    page_size=25,
                    row_deletable=False,
                    markdown_options={"link_target": "_blank"},  # Add this line
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER,
                    style_data_conditional=[
                        {
                            "if": {"column_id": col["id"]},
                            "backgroundColor": "#f0f0f0",
                            "color": "black"
                        } for col in UP_SAMPLE_FIELDS if not col["editable"]
                    ],
                )], style={"padding": "10px"})
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
                            value="SF",
                            placeholder="Select category",
                            style={"width": "100%"}
                        )
                    ], width=2),

                    dbc.Col([
                        dbc.Label("Development Stage:"),
                        dcc.Dropdown(
                            id="cld-dev-stage",
                            options=[
                                {"label": "MP", "value": "MP"},
                                {"label": "pMP", "value": "pMP"},
                                {"label": "BP", "value": "BP"},
                                {"label": "BP SCC", "value": "BP SCC"},
                                {"label": "MP SCC", "value": "MP SCC"},
                            ],
                            value="MP",
                            placeholder="Select category",
                            style={"width": "100%"}
                        )
                    ], width=2),

                    dbc.Col([
                        dbc.Label("CLD Analyst"),
                        dcc.Dropdown(
                            id="cld-analyst",
                            options=[
                                {"label": "YY", "value": "YY"},
                                {"label": "JS", "value": "JS"},
                                {"label": "YW", "value": "YW"},
                            ],

                            placeholder="Select category",
                            style={"width": "100%"}
                        )
                    ], width=2),

                ], className="mb-4 g-2"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("SIP#:"),
                        dcc.Input(id="sip-number", type="number",
                                  placeholder="SIP#", style={"width": "100%"})
                    ], width=2),
                    dbc.Col([
                        dbc.Label("UNIFI#:"),
                        dcc.Input(id="unifi-number", type="number",
                                  placeholder="UNIFI#", style={"width": "100%"})
                    ], width=2),
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
                        {"name": "Sample Number", "id": "sample_number", "editable": True},
                        {"name": "Clone", "id": "cell_line", "editable": True},
                        {"name": "Harvest Date (YYYY-MM-DD)", "id": "harvest_date", "editable": True,
                         "type": "datetime"},
                        {"name": "Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
                        {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
                        {"name": "ProAqa Eluate Titer", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
                        {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
                        {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
                        {"name": "Eluate Volume", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
                        {"name": "Fast ProAaq Recovery", "id": "fast_pro_a_recovery", "editable": False,
                         "type": "numeric"},
                        {"name": "A280 Recovery", "id": "purification_recovery_a280", "editable": False,
                         "type": "numeric"},
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


# View Sample Sets Tab Logic
@app.callback(
    Output("sample-set-table", "data"),
    Output("sample-set-table-status", "children"),
    Input("upstream-tabs", "value"),
    prevent_initial_call=False
)
def load_sample_sets(tab):
    if tab != "sample-sets-tab":
        raise PreventUpdate

    from collections import defaultdict
    from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, LimsSecResult

    fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2)
    grouped = defaultdict(list)
    for s in fb_samples:
        key = (s.project, s.sip_number, s.development_stage)
        grouped[key].append(s.sample_number)

    all_sample_ids = [f"FB{n}" for s in fb_samples for n in [s.sample_number]]
    analysis_map = {
        sa.sample_id: sa for sa in LimsSampleAnalysis.objects.filter(sample_id__in=all_sample_ids)
    }
    sec_result_ids = set(
        sr.sample_id_id for sr in LimsSecResult.objects.filter(sample_id__in=analysis_map.keys())
    )

    table_data = []
    for (project, sip, dev_stage), sample_nums in grouped.items():
        if not sample_nums:
            continue

        sorted_nums = sorted(sample_nums)
        sample_ids = [f"FB{n}" for n in sorted_nums]
        sample_range = f"FB{sorted_nums[0]} to FB{sorted_nums[-1]}"

        num_with_sec = sum(1 for sid in sample_ids if sid in sec_result_ids)
        all_have_sec = num_with_sec == len(sample_ids)

        if all_have_sec:
            view_link = "[🔬 View SEC](/plotly_integration/dash-app/app/SecReportApp2/?report_id=1)"
        else:
            view_link = "⚠️ [🔬 View SEC](/plotly_integration/dash-app/app/SecReportApp2/?report_id=1)"

        table_data.append({
            "project": project or "",
            "sip": sip or "",
            "development_stage": dev_stage or "",
            "range": sample_range,
            "count": len(sample_ids),
            "view_sec_link": view_link,
            "view_sec": "▶️ View SEC",
            "sample_ids": sample_ids
        })

    return table_data, f"🔄 Loaded {len(table_data)} FB sample sets"


# @app.callback(
#     Output("report-update-status", "children"),
#     Input("sample-set-table", "active_cell"),
#     State("sample-set-table", "data"),
#     prevent_initial_call=True
# )
# def update_temp_report_id(active_cell, table_data):
#     from plotly_integration.models import Report, LimsSecResult
#     from collections import Counter
#     print(active_cell)
#     if not active_cell:
#         raise PreventUpdate
#
#     row = table_data[active_cell["row"]]
#     sample_ids = row.get("sample_ids", [])
#     sample_set_str = ",".join(sample_ids)
#
#     # Step 1: Fetch SEC results for the selected samples
#     sec_results = LimsSecResult.objects.filter(sample_id__sample_id__in=sample_ids)
#
#     # Step 2: Count associated report_ids
#     report_id_counts = Counter()
#     for result in sec_results:
#         if result.report_id:
#             report_id_counts[result.report_id] += 1
#
#     # Step 3: Determine most common report_id
#     most_common_report_id = None
#     if report_id_counts:
#         most_common_report_id, _ = report_id_counts.most_common(1)[0]
#
#     # Step 4: Pull settings from best-matching report
#     if most_common_report_id:
#         try:
#             source_report = Report.objects.get(report_id=most_common_report_id)
#             selected_result_ids = source_report.selected_result_ids or ""
#             comments = source_report.comments or ""
#             plot_settings = source_report.plot_settings if hasattr(source_report, "plot_settings") else None
#         except Report.DoesNotExist:
#             selected_result_ids = ""
#             comments = ""
#             plot_settings = None
#     else:
#         selected_result_ids = ""
#         comments = ""
#         plot_settings = None
#
#     # Step 5: Overwrite report ID 1
#     try:
#         report = Report.objects.get(report_id=1)
#         report.project_id = row.get("project")
#         report.analysis_type = 1
#         report.sample_type = "FB"
#         report.selected_samples = sample_set_str
#         report.selected_result_ids = selected_result_ids
#         report.comments = comments
#         report.plot_settings = plot_settings
#         report.save()
#     except Report.DoesNotExist:
#         return "❌ Report ID 1 not found."
#
#     return f"✅ Report ID 1 updated using Report ID {most_common_report_id or 'None'} with {len(sample_ids)} samples"


@app.callback(
    Output("sec-redirect", "href"),
    Output("report-update-status", "children"),
    Input("sample-set-table", "active_cell"),
    State("sample-set-table", "data"),
    prevent_initial_call=True
)
def create_temp_report_and_redirect(active_cell, table_data):
    from plotly_integration.models import Report, LimsSecResult
    from collections import Counter

    if not active_cell:
        raise PreventUpdate

    row = table_data[active_cell["row"]]
    clicked_col = active_cell["column_id"]
    if clicked_col != "view_sec":
        raise PreventUpdate

    sample_ids = row.get("sample_ids", [])
    sample_set_str = ",".join(sample_ids)

    # Find the most common report_id used in LimsSecResult for these samples
    sec_results = LimsSecResult.objects.filter(sample_id__sample_id__in=sample_ids)
    report_counts = Counter(r.report_id for r in sec_results if r.report_id)

    best_report_id = report_counts.most_common(1)[0][0] if report_counts else None

    # Get settings from the best report, if available
    selected_result_ids = comments = ""
    plot_settings = None
    if best_report_id:
        try:
            source = Report.objects.get(report_id=best_report_id)
            selected_result_ids = source.selected_result_ids or ""
            comments = source.comments or ""
            plot_settings = getattr(source, "plot_settings", None)
        except Report.DoesNotExist:
            pass

    report_fields = {
        "report_name": "__temp_fb_view_report__",
        "analysis_type": 1,
        "sample_type": "FB",
        "project_id": row.get("project"),
        "selected_samples": sample_set_str,
        "selected_result_ids": selected_result_ids,
        "comments": comments,
        "plot_settings": plot_settings,
    }

    # Update if report_id=1 exists
    updated = Report.objects.filter(report_id=1).update(**report_fields)

    # Otherwise, force-create it
    if updated == 0:
        temp_report = Report(report_id=1, **report_fields)
        temp_report.save(force_insert=True)

    return "/plotly_integration/dash-app/app/SecReportApp2/?report_id=1", \
           f"✅ Temp SEC report (ID 1) updated with {len(sample_ids)} samples"
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
                    sample_number=row["sample_number"], sample_type=2
                ).update(**update_data)
                updated += 1
            except Exception as e:
                print(f"Update failed for sample {row.get('sample_number')}: {e}")
                errors += 1

    # Always reload data, sorted by descending sample_number
    samples = LimsUpstreamSamples.objects.filter(sample_type=2).order_by("-sample_number")
    new_data = []
    for s in samples:
        fast_pro_a, a280 = calculate_recoveries(s)
        row = {}
        for field in FIELD_IDS:
            if field == "harvest_date":
                value = getattr(s, field, None)
                row[field] = value.strftime("%Y-%m-%d") if value else None
            elif field != "report_link":  # Avoid getattr for dynamic fields
                row[field] = getattr(s, field, None)

        row["fast_pro_a_recovery"] = fast_pro_a
        row["purification_recovery_a280"] = a280

        analysis = LimsSampleAnalysis.objects.filter(sample_id=f"FB{s.sample_number}").first()
        if analysis and analysis.sec_result and analysis.sec_result.report_id:
            report_id = analysis.sec_result.report_id
            row[
                "report_link"] = f'[🔗 SEC Report](/plotly_integration/dash-app/app/SecReportApp2/?report_id={report_id})'
        else:
            row["report_link"] = ""

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
def modify_sample_table(add_ts, clear_ts, current_data):
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
        db_max = LimsUpstreamSamples.objects.filter(sample_type=2).aggregate(Max("sample_number"))
        max_sample_number = db_max["sample_number__max"] or 0

        # Check in-memory data
        current_numbers = [
            int(row["sample_number"]) for row in current_data
            if str(row.get("sample_number")).isdigit()
        ]
        if current_numbers:
            max_sample_number = max(max_sample_number, max(current_numbers))

        next_sample_number = max_sample_number + 1

        current_data.append({
            "sample_number": next_sample_number,
            # "project": "",
            # "vessel_type": "",
            # "experiment_number": "",
            # "sip_number": "",
            # "unifi_number": "",
            # "development_stage": "",
            # "analyst": "",
            "cell_line": "",
            # "culture_duration": "",
            # "description": "",
            "harvest_date": "",
            "hf_octet_titer": "",
            "pro_aqa_hf_titer": "",
            "pro_aqa_e_titer": "",
            "proa_eluate_a280_conc": "",
            "hccf_loading_volume": "",
            "proa_eluate_volume": "",
            # "fast_pro_a_recovery": "",
            # "purification_recovery_a280": "",
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
    State("cld-dev-stage", "value"),
    State("cld-analyst", "value"),
    State("sip-number", "value"),
    State("unifi-number", "value"),

    prevent_initial_call=True
)
def save_up_samples(save_up_ts, table_data, project, vessel_type, dev_stage, analyst, sip_number, unifi_number):
    from plotly_integration.models import LimsUpstreamSamples
    # print(project, vessel_type, dev_stage, analyst, sip_number, unifi_number)
    if not table_data:
        return "❌ No data to save."
    if not project or not vessel_type:
        return "⚠️ Please fill in Project and Vessel Type."

    print(f"💾 Saving UP samples for project '{project}' | vessel: {vessel_type}")

    created, skipped, errors = 0, 0, 0

    for row in table_data:
        try:
            sample_number = row.get("sample_number")
            if not sample_number:
                skipped += 1
                continue

            _, created_flag = LimsUpstreamSamples.objects.update_or_create(
                sample_number=sample_number,
                sample_type=2,
                defaults={
                    "project": project,
                    "vessel_type": vessel_type,
                    "sip_number": sip_number,
                    "unifi_number": unifi_number,
                    "development_stage": dev_stage,
                    "analyst": analyst,
                    "cell_line": row.get("cell_line") or "",
                    "harvest_date": row.get("harvest_date") or None,
                    "hf_octet_titer": row.get("hf_octet_titer") or None,
                    "pro_aqa_hf_titer": row.get("pro_aqa_hf_titer") or None,
                    "pro_aqa_e_titer": row.get("pro_aqa_e_titer") or None,
                    "proa_eluate_a280_conc": row.get("proa_eluate_a280_conc") or None,
                    "hccf_loading_volume": row.get("hccf_loading_volume") or None,
                    "proa_eluate_volume": row.get("proa_eluate_volume") or None,
                    "note": row.get("note") or "",
                }
            )

            LimsSampleAnalysis.objects.update_or_create(
                sample_id=f'FB{row["sample_number"]}',
                sample_type=2,
                defaults={
                    "sample_date": row.get("harvest_date") or None,
                    "project_id": project,
                    "description": row.get("description", ""),
                    "notes": row.get("note", ""),
                    "dn": None,
                    "a280_result": None
                }
            )

            created += 1 if created_flag else 0

        except Exception as e:
            print(f"❌ Error saving sample {row.get('sample_number')}: {e}")
            errors += 1

    return f"✅ Created/Updated: {created} | Skipped: {skipped} | Errors: {errors}"
