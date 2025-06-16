from plotly_integration.models import LimsSampleAnalysis, LimsSecResult, LimsTiterResult, LimsMassCheckResult, LimsReleasedGlycanResult, LimsHcpResult, LimsProaResult, LimsCiefResult, LimsCeSdsResult
import pandas as pd
import dash
from dash import dcc, html, Input, Output, State, dash_table, ctx, callback_context
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

app = DjangoDash("SampleAnalysisApp", external_stylesheets=[dbc.themes.BOOTSTRAP])

ANALYTIC_MODELS = {
    "SEC": (LimsSecResult, ["main_peak", "hmw", "lmw"]),
    "Titer": (LimsTiterResult, ["titer"]),
    "Mass Check": (LimsMassCheckResult, ["expected_mass", "observed_mass"]),
    "Glycan": (LimsReleasedGlycanResult, ["major_species"]),
    "HCP": (LimsHcpResult, ["hcp_level"]),
    "ProA": (LimsProaResult, ["proa_level"]),
    "CIEF": (LimsCiefResult, ["main_peak", "acidic_variants", "basic_variants"]),
    "CE-SDS": (LimsCeSdsResult, ["purity"]),
}

def get_result_status(sample, model, fields):
    try:
        result = model.objects.get(sample_id=sample)
        return result.status, [getattr(result, f, "N/A") for f in fields]
    except model.DoesNotExist:
        return "in_progress", ["Analytical in progress"] * len(fields)

app.layout = html.Div([
    dcc.Store(id="sample-context", data={"mode": "", "sample_id": ""}),
    html.Div([
        dcc.Tabs(id="sample-tabs", value="select-tab", children=[
            dcc.Tab(label="Select Sample", value="select-tab", children=[
                html.Div([
                    html.Div([
                        dbc.Button("Refresh Table", id="refresh-sample-table", size="sm", color="secondary", className="me-2"),
                        dbc.Button("Create New Sample", id="create-new-sample", size="sm", color="primary")
                    ], className="mb-2 d-flex gap-2"),
                    dash_table.DataTable(
                        id="sample-table",
                        columns=[],
                        data=[],
                        row_selectable="single",
                        page_action="native",
                        page_size=20,
                        style_table={"height": "75vh", "overflowY": "auto"},
                        style_cell={"textAlign": "left", "fontSize": "11px", "padding": "2px"},
                        style_header={"backgroundColor": "#0d6efd", "color": "white", "fontWeight": "bold"}
                    )
                ], style={"padding": "10px"})
            ]),
            dcc.Tab(label="Sample Details", value="edit-tab", children=[
                html.Div([
                    dbc.Row([
                        dbc.Col(dbc.Input(id="sample_id", placeholder="Sample ID", type="text", size="sm"), width=4),
                        dbc.Col(dbc.Input(id="project_id", placeholder="Project ID", type="text", size="sm"), width=4),
                        dbc.Col(dbc.Input(id="analyst", placeholder="Analyst", type="text", size="sm"), width=4),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col(dbc.Input(id="sample_date", placeholder="Sample Date (YYYY-MM-DD)", type="text", size="sm"), width=6),
                        dbc.Col(dbc.Input(id="run_date", placeholder="Run Date (YYYY-MM-DD)", type="text", size="sm"), width=6),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col(dbc.Textarea(id="sample_notes", placeholder="Notes", rows=2), width=12)
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col(dbc.Button("Save Sample", id="save-sample", color="primary", size="sm"), width="auto"),
                        dbc.Col(html.Div(id="sample-save-status", style={"fontSize": "11px", "marginTop": "5px"}), width="auto"),
                    ]),
                    html.Hr(),
                    html.Div(id="analytic-sections")
                ], style={"padding": "10px"})
            ])
        ])
    ])
])

@app.callback(
    Output("sample-tabs", "value"),
    Output("sample-context", "data"),
    Input("create-new-sample", "n_clicks"),
    Input("sample-table", "selected_rows"),
    State("sample-table", "data"),
    prevent_initial_call=True
)
def switch_tab(n_create, selected_rows, table_data):
    if n_create:
        return "edit-tab", {"mode": "create", "sample_id": ""}

    if selected_rows and table_data:
        selected = table_data[selected_rows[0]]
        return "edit-tab", {"mode": "edit", "sample_id": selected["sample_id"]}

    raise PreventUpdate

@app.callback(
    Output("sample_id", "value"),
    Output("project_id", "value"),
    Output("analyst", "value"),
    Output("sample_date", "value"),
    # REMOVE run_date output
    Output("sample_notes", "value"),
    Input("sample-context", "data"),
    prevent_initial_call=True
)
def populate_sample_form(context):
    if not context or "sample_id" not in context:
        raise PreventUpdate

    if context["mode"] == "create":
        return "", "", "", "", ""

    try:
        sample = LimsSampleAnalysis.objects.get(sample_id=context["sample_id"])
        return (
            sample.sample_id,
            sample.project_id,
            sample.analyst,
            str(sample.sample_date) if sample.sample_date else "",
            sample.notes
        )
    except LimsSampleAnalysis.DoesNotExist:
        return "", "", "", "", ""

@app.callback(
    Output("sample-save-status", "children"),
    Input("save-sample", "n_clicks"),
    State("sample_id", "value"),
    State("project_id", "value"),
    State("analyst", "value"),
    State("sample_date", "value"),
    State("run_date", "value"),
    State("sample_notes", "value"),
    State("sample-context", "data"),
    prevent_initial_call=True
)
def save_sample(n, sample_id, project_id, analyst, sample_date, run_date, notes, context):
    try:
        obj, created = LimsSampleAnalysis.objects.update_or_create(
            sample_id=sample_id,
            defaults={
                "project_id": project_id,
                "analyst": analyst,
                "sample_date": sample_date,
                "run_date": run_date,
                "notes": notes
            }
        )
        return "✅ Sample created" if created else "✅ Sample updated"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.callback(
    Output("sample-table", "columns"),
    Output("sample-table", "data"),
    Input("refresh-sample-table", "n_clicks"),
    Input("sample-tabs", "value"),
    Input("sample-table", "page_current"),
    Input("sample-table", "page_size"),
    prevent_initial_call=False
)
def refresh_sample_table(n_clicks, tab_value, page_current, page_size):
    if tab_value != "select-tab":
        raise dash.exceptions.PreventUpdate

    # --- Set defaults if None ---
    page_current = page_current or 0
    page_size = page_size or 20

    all_samples = LimsSampleAnalysis.objects.all()

    # Sort descending by numeric value of sample_id
    def sort_key(s):
        try:
            return int(str(s.sample_id).lstrip("PD").lstrip("0") or "0")
        except:
            return 0

    sorted_samples = sorted(all_samples, key=sort_key, reverse=True)

    # Apply pagination
    start = page_current * page_size
    end = start + page_size
    paginated_samples = sorted_samples[start:end]

    data = []
    for s in paginated_samples:
        sec_status, sec_vals = get_result_status(s, LimsSecResult, ["main_peak", "hmw", "lmw"])
        titer_status, titer_vals = get_result_status(s, LimsTiterResult, ["titer"])
        hcp_status, hcp_vals = get_result_status(s, LimsHcpResult, ["hcp_level"])
        proa_status, proa_vals = get_result_status(s, LimsProaResult, ["proa_level"])
        row = {
            "sample_id": s.sample_id,
            "project_id": s.project_id,
            "a280": s.a280_result,
            "SEC Main": sec_vals[0],
            "HMW": sec_vals[1],
            "LMW": sec_vals[2],
            "Titer": titer_vals[0],
            "HCP": hcp_vals[0],
            "ProA": proa_vals[0],
        }
        data.append(row)

    columns = [{"name": col, "id": col} for col in data[0].keys()] if data else []
    return columns, data

@app.callback(
    Output("analytic-sections", "children"),
    Input("sample-context", "data"),
    prevent_initial_call=True
)
def render_analytic_cards(context):
    if context["mode"] != "edit":
        return html.Div("Sample not yet saved. Please save first.")
    sample = LimsSampleAnalysis.objects.filter(sample_id=context["sample_id"]).first()
    if not sample:
        return html.Div("Sample not found.")
    cards = []
    for name, (model, fields) in ANALYTIC_MODELS.items():
        try:
            r = model.objects.get(sample_id=sample)
            body = [html.P(f"{f.replace('_', ' ').title()}: {getattr(r, f)}") for f in fields]
            card = dbc.Card([
                dbc.CardHeader(f"{name} (Status: {r.status})", style={"backgroundColor": "#e9ecef"}),
                dbc.CardBody(body)
            ], className="mb-3")
        except model.DoesNotExist:
            card = dbc.Card([
                dbc.CardHeader(f"{name} (Analytical in progress)", style={"backgroundColor": "#fff3cd"}),
                dbc.CardBody(html.P("No data yet."))
            ], className="mb-3", color="warning", outline=True)
        cards.append(card)
    return cards
