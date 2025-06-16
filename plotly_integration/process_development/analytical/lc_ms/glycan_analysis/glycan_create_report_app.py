import re
import pandas as pd
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
from plotly_integration.models import ReleasedGlycanResult, GlycanReport
from datetime import datetime
from django.utils.timezone import is_aware


app = DjangoDash("CreateGlycanReportApp")

# Fetch available results
results = ReleasedGlycanResult.objects.all().order_by("-uploaded_at")
columns = [
    {"name": "Result ID", "id": "result_id"},
    {"name": "Result Name", "id": "result_name"},
    {"name": "Uploaded", "id": "uploaded_at"},
]
data = []
for result in results:
    data.append({
        "result_id": result.result_id,
        "result_name": result.result_name,
        "uploaded_at": result.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if result.uploaded_at else ""
    })

# Layout
app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "backgroundColor": "#f4f7f6", "padding": "20px",
           "maxWidth": "1200px", "margin": "0 auto", "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)", "borderRadius": "8px"},
    children=[
        html.H1("Released Glycan Report Creator", style={"textAlign": "center", "color": "#0047b3", "marginBottom": "20px"}),

        # Filter Section
        html.Div(style={"marginBottom": "20px"}, children=[
            html.Label("Filter by Sample Type:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="sample_type_filter",
                options=[
                    {"label": "UP", "value": "1"},
                    {"label": "CLD", "value": "2"},
                    {"label": "Uncategorized", "value": "3"},
                ],
                placeholder="Select sample type",
                multi=False,
                clearable=True,
                style={"marginBottom": "10px"},
            ),

            html.Label("Filter by Experiment Number:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="experiment_number_filter",
                options=[],  # ✅ Dynamically populated
                placeholder="Select experiment number(s)",
                multi=True,  # ✅ Allow multiple selections
                clearable=True,
                style={"marginBottom": "20px"},
            )
        ]),

        # Table with Select All Button
        html.Button("Select All", id="select_all_button", n_clicks=0,
                    style={"marginBottom": "10px", "backgroundColor": "#0047b3", "color": "white",
                           "padding": "5px 10px", "border": "none", "borderRadius": "5px", "cursor": "pointer"}),

        dash_table.DataTable(
            id="sample_table",
            columns=columns,
            data=data,
            row_selectable="multi",
            selected_rows=[],
            page_size=15,
            filter_action="native",
            sort_action="native",
            sort_mode="multi"
        ),

        # Report Form
        html.Div(children=[
            html.H2("Create Report", style={"color": "#0047b3", "marginTop": "20px"}),

            html.Label("Report Name:", style={"fontWeight": "bold"}),
            dcc.Input(id="report_name_input", type="text", placeholder="Enter report name",
                      style={"width": "100%", "marginBottom": "10px"}),

            html.Label("Project ID:", style={"fontWeight": "bold"}),
            dcc.Input(id="project_id_input", type="text", placeholder="Enter project ID",
                      style={"width": "100%", "marginBottom": "10px"}),

            html.Label("User ID:", style={"fontWeight": "bold"}),
            dcc.Input(id="user_id_input", type="text", placeholder="Enter user ID",
                      style={"width": "100%", "marginBottom": "10px"}),

            html.Label("Comments:", style={"fontWeight": "bold"}),
            dcc.Textarea(id="comments_input", placeholder="Enter comments",
                         style={"width": "100%", "marginBottom": "10px"}),

            html.Button("Create Report", id="create_report_button", n_clicks=0,
                        style={"backgroundColor": "#28a745", "color": "white", "padding": "10px 20px",
                               "border": "none", "borderRadius": "5px", "cursor": "pointer", "fontSize": "16px"}),

            html.Div(id="report_status", style={"marginTop": "10px", "fontWeight": "bold", "color": "green"})
        ])
    ]
)

# ✅ Fix Select All Button Callback
@app.callback(
    Output("sample_table", "selected_rows"),
    Input("select_all_button", "n_clicks"),
    State("sample_table", "data"),
    prevent_initial_call=True
)
def select_all_rows(n_clicks, data):
    if not data:
        return []  # ✅ No data → return empty list

    # ✅ Toggle logic: Select all if odd clicks, Deselect all if even
    if n_clicks % 2 == 1:
        return list(range(len(data)))  # ✅ Select all rows
    return []  # ✅ Deselect all rows


# ✅ Update Experiment Number Dropdown (Re-query Every Time)
@app.callback(
    Output("experiment_number_filter", "options"),
    Input("sample_type_filter", "value")
)
def update_experiment_options(selected_sample_type):
    if not selected_sample_type:
        return []

    # ✅ Fetch unique experiment numbers and sort descending
    experiment_numbers = (
        ReleasedGlycanResult.objects.filter(sample_type=selected_sample_type)
        .exclude(experiment__isnull=True)
        .values_list("experiment", flat=True)
        .distinct()
        .order_by("-experiment")  # ✅ Sorting directly in database
    )

    return [{"label": str(exp), "value": str(exp)} for exp in experiment_numbers]


# ✅ Update Table Based on Filters (Re-query Every Time)
@app.callback(
    Output("sample_table", "data"),
    [Input("sample_type_filter", "value"),
     Input("experiment_number_filter", "value")]
)
def update_table(selected_sample_type, selected_experiment_numbers):
    query = ReleasedGlycanResult.objects.all().order_by("-uploaded_at")  # ✅ Sort by most recent first

    if selected_sample_type:
        query = query.filter(sample_type=selected_sample_type)

    if selected_experiment_numbers:
        query = query.filter(experiment__in=selected_experiment_numbers)  # ✅ Handle multiple selections

    # ✅ Convert queryset to list of dictionaries
    data = list(query.values(
         "sample_id", "sample_type", "uploaded_at",
    ))

    # ✅ Format datetime for display
    for row in data:
        if row["uploaded_at"]:
            row["uploaded_at"] = row["uploaded_at"].strftime("%m/%d/%Y %I:%M:%S %p")

    return data


# ✅ Create GlycanReport Report Callback
@app.callback(
    Output("report_status", "children"),
    Input("create_report_button", "n_clicks"),
    [State("report_name_input", "value"),
     State("project_id_input", "value"),
     State("user_id_input", "value"),
     State("comments_input", "value"),
     State("sample_table", "data"),
     State("sample_table", "selected_rows")],
    prevent_initial_call=True
)
def create_report(n_clicks, report_name, project_id, user_id, comments, table_data, selected_rows):
    if not report_name or not selected_rows:
        return "❌ Please provide a report name and select at least one row."

    selected_result_ids = [table_data[i]["result_id"] for i in selected_rows]
    selected_result_names = [table_data[i]["result_name"] for i in selected_rows]

    GlycanReport.objects.create(
        report_name=report_name,
        project_id=project_id,
        user_id=user_id,
        comments=comments,
        selected_result_ids=",".join(map(str, selected_result_ids)),
        selected_glycan_names=",".join(map(str, selected_result_names))
    )

    return "✅ GlycanReport Report created successfully!"
