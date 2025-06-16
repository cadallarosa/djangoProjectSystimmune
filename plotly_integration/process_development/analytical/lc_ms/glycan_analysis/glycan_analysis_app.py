import pandas as pd
import numpy as np
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
from plotly_integration.models import GlycanReport, ReleasedGlycanResult, ReleasedGlycanComponent
from django.utils.timezone import localtime

app = DjangoDash("GlycanReportAnalysisApp")

app.layout = html.Div([
    html.H2("Glycan Report Analysis", style={"textAlign": "center", "color": "#0047b3"}),

    html.Label("Select a Report:"),
    dcc.Dropdown(
        id="report_selector",
        options=[],
        placeholder="Select a Glycan Report",
        style={"marginBottom": "20px"}
    ),

    html.Div(id="report_metadata", style={"marginBottom": "20px"}),

    dcc.Tabs(id="main-tabs", value="tab-1", children=[

        # 🔹 Tab 1: Table Tab
        dcc.Tab(label="Table", value="tab-1", children=[

            html.H4("Component Percent Table"),
            dash_table.DataTable(
                id="glycan_table",
                columns=[],
                data=[],
                page_size=50,
                sort_action="native",
                style_table={"overflowX": "auto"},
                style_header={"backgroundColor": "#0047b3", "color": "white"},
                style_cell={"textAlign": "center", "padding": "8px"},
            ),
            html.Button("Export Table as CSV", id="export_btn", style={"marginTop": "20px"}),
            dcc.Download(id="download_data"),

        ]),
        # 🔹 Tab 2: Chart Tab
        dcc.Tab(label="Chart", value="tab-2", children=[

            dcc.Graph(id="stacked_bar_chart", style={"marginTop": "40px"}),
        ]),
    ])

])


@app.callback(
    Output("report_selector", "options"),
    Input("report_selector", "id")  # dummy input to trigger on page load
)
def update_report_dropdown(_):
    reports = GlycanReport.objects.all().order_by("-created_at")
    return [
        {"label": f"{r.report_name} ({localtime(r.created_at).strftime('%Y-%m-%d %H:%M')})", "value": r.id}
        for r in reports
    ]


@app.callback(
    [Output("glycan_table", "columns"),
     Output("glycan_table", "data"),
     Output("report_metadata", "children"),
     Output("stacked_bar_chart", "figure")],
    Input("report_selector", "value")
)
def update_report(report_id):
    if not report_id:
        return [], [], "", {}

    report = GlycanReport.objects.get(id=report_id)
    result_ids = report.selected_result_ids.split(",")
    results = ReleasedGlycanResult.objects.filter(result_id__in=result_ids)
    components = ReleasedGlycanComponent.objects.filter(result_id__in=result_ids)

    df = pd.DataFrame.from_records(components.values(
        "result_id", "component_name", "observed_rt_min", "percent_amount"
    ))
    df = df.merge(
        pd.DataFrame.from_records(results.values("result_id", "result_name")),
        on="result_id",
        how="left"
    )

    # Calculate average RT per component
    avg_rt = round(df.groupby("component_name", as_index=False)["observed_rt_min"].mean(), 2)

    # Pivot the percent_amount values into columns per result
    pivot = df.pivot_table(
        index="component_name",
        columns="result_name",
        values="percent_amount",
        aggfunc="sum",  # or 'mean' if more appropriate
        fill_value=0
    ).reset_index()

    # Merge in average RT for display
    pivot_table = avg_rt.merge(pivot, on="component_name")
    pivot_table = pivot_table.sort_values("observed_rt_min")

    # Prepare DataTable columns
    columns = [
                  {"name": "Component name", "id": "component_name"},
                  {"name": "Observed RT (min)", "id": "observed_rt_min"},
              ] + [{"name": col, "id": col} for col in pivot_table.columns if
                   col not in ["component_name", "observed_rt_min"]]

    metadata = html.Div([
        html.P(f"Report Name: {report.report_name}"),
        html.P(f"User: {report.user_id}"),
        html.P(f"Comments: {report.comments}"),
        html.P(f"Created: {localtime(report.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
    ])

    # Bar chart with components on x-axis, grouped bars per result (ordered by RT)
    melt_df = df.pivot_table(index=["component_name", "observed_rt_min"], columns="result_name",
                             values="percent_amount", fill_value=0).reset_index()
    melt_df = melt_df.sort_values("observed_rt_min")

    bar_fig = {
        "data": [
            {"x": melt_df["component_name"], "y": melt_df[col], "type": "bar", "name": col}
            for col in melt_df.columns if col not in ["component_name", "observed_rt_min"]
        ],
        "layout": {
            "barmode": "group",
            "title": "Glycan % Amount by Component (Ordered by RT)",
            "xaxis": {"title": "Glycan Component", "automargin": True},
            "yaxis": {"title": "% Amount"},
        }
    }

    return columns, pivot_table.to_dict("records"), metadata, bar_fig


@app.callback(
    Output("download_data", "data"),
    Input("export_btn", "n_clicks"),
    State("glycan_table", "data"),
    prevent_initial_call=True
)
def export_table(n_clicks, table_data):
    if not table_data:
        return None
    df = pd.DataFrame(table_data)
    return dcc.send_data_frame(df.to_csv, filename="glycan_report_summary.csv", index=False)
