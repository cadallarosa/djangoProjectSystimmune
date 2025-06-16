import pandas as pd
import numpy as np
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
import plotly.express as px
import plotly.graph_objs as go
from plotly_integration.models import MassCheckReport, MassCheckResult, MassCheckComponent
from django.utils.timezone import localtime

app = DjangoDash("MassCheckAnalysisApp")

app.layout = html.Div([
    html.H2("Mass Check Analysis", style={"textAlign": "center", "color": "#0047b3"}),

    html.Label("Select a Report:"),
    dcc.Dropdown(id="report_selector", options=[], placeholder="Select a Report"),

    html.Div(id="report_metadata", style={"margin": "10px 0"}),

    dcc.Tabs(id="tabs", value="table", children=[
        dcc.Tab(label="Component Table", value="table"),
        dcc.Tab(label="Mass Error by Protein", value="boxplot"),
        # dcc.Tab(label="Delta Mass Histogram", value="histogram"),

    ]),

    html.Div(id="tab-content"),

    html.Button("Export Table to Excel", id="export-button", style={"marginTop": "10px"}),
    dcc.Download(id="download-data")
])


@app.callback(
    Output("report_selector", "options"),
    Input("report_selector", "id")
)
def load_reports(_):
    reports = MassCheckReport.objects.order_by("-created_at")
    return [{"label": f"{r.report_name} ({localtime(r.created_at).strftime('%Y-%m-%d')})", "value": r.id} for r in
            reports]


@app.callback(
    Output("report_metadata", "children"),
    Input("report_selector", "value")
)
def display_metadata(report_id):
    """
    Updates and displays metadata of the selected report.

    This function is a callback for a Dash application. It dynamically
    updates the metadata display for a selected report when the user
    chooses a report from the selector. The metadata includes the project
    ID, department, and comments associated with the specific report. If no
    report is selected, it returns an empty string.

    :param report_id: The ID of the report selected in the "report_selector".
    :type report_id: str
    :return: A Div element containing metadata information if the report is
             found, or an empty string if no report is selected.
    :rtype: Union[str, dash.development.base_component.Component]
    """
    if not report_id:
        return ""
    report = MassCheckReport.objects.get(id=report_id)
    return html.Div([
        html.P(f"Project ID: {report.project_id}"),
        html.P(f"Department: {report.department}"),
        html.P(f"Comments: {report.comments}")
    ])


@app.callback(
    Output("tab-content", "children"),
    [Input("report_selector", "value"), Input("tabs", "value")]
)
def update_tab(report_id, tab):
    if not report_id:
        return "Please select a report."

    report = MassCheckReport.objects.get(id=report_id)
    result_ids = [rid.strip() for rid in report.selected_result_ids.split(",") if rid.strip()]
    components = MassCheckComponent.objects.filter(result__result_id__in=result_ids)

    df = pd.DataFrame.from_records(components.values(
        'result__result_name', 'protein_name', 'expected_mass_da', 'observed_mass_da',
        'mass_error_mda', 'mass_error_ppm', 'observed_rt_min', 'response'
    ))
    df.rename(columns={"result__result_name": "result_name"}, inplace=True)

    if df.empty:
        return "No component data available."

    if tab == "scatter":
        fig = px.scatter(df, x="observed_mass_da", y="mass_error_ppm",
                         hover_data=["protein_name", "response", "observed_rt_min"],
                         color="protein_name",
                         title="Mass Accuracy (ppm)")
        return dcc.Graph(figure=fig)

    elif tab == "boxplot":
        fig = px.box(df, x="protein_name", y="mass_error_mda",
                     title="Mass Error by Protein")
        return dcc.Graph(figure=fig)


    elif tab == "histogram":
        df["delta_mass"] = df["observed_mass_da"] - df["expected_mass_da"]
        fig = px.histogram(df, x="delta_mass", nbins=50,
                           title="Delta Mass Histogram (Observed - Expected)")
        return dcc.Graph(figure=fig)

    # elif tab == "table":
    #     columns = [{"name": i, "id": i} for i in df.columns]
    #     return dash_table.DataTable(
    #         columns=columns,
    #         data=df.to_dict("records"),
    #         page_size=15,
    #         filter_action="native",
    #         sort_action="native",
    #         style_table={"overflowX": "auto"},
    #         style_cell={"textAlign": "center", "padding": "5px"},
    #         id="component-table"
    #     )

    elif tab == "table":
        # Calculate average absolute mass error per result group
        df["abs_mass_error_mda"] = df["mass_error_mda"].abs()

        avg_error_per_result = df.groupby("result_name")["abs_mass_error_mda"].mean().reset_index()
        avg_error_per_result.rename(columns={"abs_mass_error_mda": "avg_abs_mass_error_mda"}, inplace=True)

        # Rank by lowest average absolute error
        avg_error_per_result["rank"] = avg_error_per_result["avg_abs_mass_error_mda"].rank(ascending=True, method="min")

        # Merge rank back to original dataframe
        df = df.merge(avg_error_per_result, on="result_name")
        df = df.sort_values(["rank", "result_name", "abs_mass_error_mda"])

        columns = [{"name": i.replace("_", " ").title(), "id": i} for i in df.columns]
        return dash_table.DataTable(
            columns=columns,
            data=df.to_dict("records"),
            page_size=15,
            filter_action="native",
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "5px"},
            id="component-table"
        )

    return "Invalid tab"


@app.callback(
    Output("download-data", "data"),
    Input("export-button", "n_clicks"),
    State("report_selector", "value"),
    prevent_initial_call=True
)
def export_table(n_clicks, report_id):
    if not report_id:
        return
    report = MassCheckReport.objects.get(id=report_id)
    result_ids = [rid.strip() for rid in report.selected_result_ids.split(",") if rid.strip()]
    components = MassCheckComponent.objects.filter(result__result_id__in=result_ids)
    df = pd.DataFrame.from_records(components.values())
    return dcc.send_data_frame(df.to_excel, "mass_check_report.xlsx", index=False)
