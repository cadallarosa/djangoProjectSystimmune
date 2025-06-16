import re
import pytz
import pandas as pd
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
from plotly_integration.models import NovaFlex2, NovaReport
from datetime import datetime
from django.utils.timezone import is_aware

# Initialize the Dash app
app = DjangoDash("NovaFlex2ReportApp")


# Function to extract experiment number from sample_id
def extract_experiment_number(sample_id):
    match = re.match(r"(E\d{2})", sample_id)  # Extracts 'E' followed by two digits (e.g., E43)
    return match.group(1) if match else "Unknown"


# Fetch default table columns and data
def get_default_columns_and_data():
    default_columns = ["id", "sample_id", "sample_type", "date_time", "gln", "glu", "gluc", "lac"]
    samples = NovaFlex2.objects.all()
    columns = [{"name": col.replace("_", " ").title(), "id": col} for col in default_columns]

    data = []
    for sample in samples:
        row = {col: getattr(sample, col, None) for col in default_columns}

        # Convert date_time if needed
        if "date_time" in row and row["date_time"]:
            dt_value = row["date_time"]
            if isinstance(dt_value, datetime) and is_aware(dt_value):
                dt_value = dt_value.replace(tzinfo=None)
            row["date_time"] = dt_value.strftime("%m/%d/%Y %I:%M:%S %p")

        # Extract experiment number
        row["experiment_number"] = extract_experiment_number(row["sample_id"])

        data.append(row)

    return columns, data


# Default table setup
default_columns, default_data = get_default_columns_and_data()

# Layout
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f4f7f6",
        "padding": "20px",
        "maxWidth": "1200px",
        "margin": "0 auto",
        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "borderRadius": "8px"
    },
    children=[
        html.H1("NovaFlex2 Report Viewer", style={"textAlign": "center", "color": "#0047b3", "marginBottom": "20px"}),

        # Filter Section
        html.Div(
            style={"marginBottom": "20px"},
            children=[
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
                    clearable=False,
                    style={"marginBottom": "10px"},
                ),

                html.Label("Filter by Experiment Number:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="experiment_number_filter",
                    options=[],  # Dynamically populated
                    placeholder="Select experiment number",
                    multi=False,
                    clearable=True,
                    style={"marginBottom": "20px"},
                )
            ]
        ),

        # Table with Select All Button
        html.Button(
            "Select All",
            id="select_all_button",
            n_clicks=0,
            style={
                "marginBottom": "10px",
                "backgroundColor": "#0047b3",
                "color": "white",
                "padding": "5px 10px",
                "border": "none",
                "borderRadius": "5px",
                "cursor": "pointer"
            }
        ),
        dash_table.DataTable(
            id="sample_table",
            columns=default_columns,
            data=default_data,
            row_selectable="multi",
            selected_rows=[],
            page_size=15,
            filter_action="native",
            sort_action="native",
            sort_mode="multi"
        ),

        # Report Form
        html.Div(
            children=[
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

                html.Button(
                    "Create Report",
                    id="create_report_button",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#28a745",
                        "color": "white",
                        "padding": "10px 20px",
                        "border": "none",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "16px"
                    }
                ),

                html.Div(id="report_status", style={"marginTop": "10px", "fontWeight": "bold", "color": "green"})
            ]
        )
    ]
)


# Select All Callback
@app.callback(
    Output("sample_table", "selected_rows"),
    Input("select_all_button", "n_clicks"),
    State("sample_table", "data")
)
def select_all_rows(n_clicks, data):
    if n_clicks % 2 == 1:
        return list(range(len(data)))  # Select all rows
    return []  # Deselect all rows


@app.callback(
    Output("experiment_number_filter", "options"),
    Input("sample_type_filter", "value")
)
def update_experiment_options(selected_sample_type):
    if not selected_sample_type:
        return []

    # Filter dataset based on sample_type
    samples = NovaFlex2.objects.filter(sample_type=selected_sample_type)

    # Extract unique experiment numbers
    experiment_numbers = set()
    for sample in samples:
        exp_number = extract_experiment_number(sample.sample_id)
        if exp_number:
            experiment_numbers.add(exp_number)

    # Sort in descending order (highest to lowest)
    sorted_experiments = sorted(experiment_numbers, reverse=True)

    return [{"label": exp, "value": exp} for exp in sorted_experiments]


# Callback: Update Table Based on Filters
@app.callback(
    Output("sample_table", "data"),
    [Input("sample_type_filter", "value"),
     Input("experiment_number_filter", "value")]
)
def update_table(selected_sample_type, selected_experiment_number):
    query = NovaFlex2.objects.all()

    # Apply sample type filter
    if selected_sample_type:
        query = query.filter(sample_type=selected_sample_type)

    # Apply experiment number filter
    if selected_experiment_number:
        query = [s for s in query if extract_experiment_number(s.sample_id) == selected_experiment_number]

    # Format data for table
    data = []
    for sample in query:
        row = {
            "id": sample.id,
            "sample_id": sample.sample_id,
            "sample_type": sample.sample_type,
            "date_time": sample.date_time.strftime("%m/%d/%Y %I:%M:%S %p") if sample.date_time else None,
            "gln": sample.gln,
            "glu": sample.glu,
            "gluc": sample.gluc,
            "lac": sample.lac,
            "experiment_number": extract_experiment_number(sample.sample_id)
        }
        data.append(row)

    return data


# Create Report Callback
@app.callback(
    Output("report_status", "children"),
    Input("create_report_button", "n_clicks"),
    [State("report_name_input", "value"),
     State("project_id_input", "value"),
     State("user_id_input", "value"),
     State("comments_input", "value"),
     State("sample_table", "data"),
     State("sample_table", "selected_rows")],
    prevent_initial_call=True  # ✅ Prevents running on page load
)
def create_report(n_clicks, report_name, project_id, user_id, comments, table_data, selected_rows):
    if not report_name or not selected_rows:
        return "❌ Please provide a report name and select at least one row."

    selected_result_ids = [table_data[i]["id"] for i in selected_rows]

    NovaReport.objects.create(
        report_name=report_name,
        project_id=project_id,
        user_id=user_id,
        comments=comments,
        selected_result_ids=",".join(map(str, selected_result_ids))
    )

    return "✅ Report created successfully!"
