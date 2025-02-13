from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
from .models import SampleMetadata, Report
from datetime import datetime


# Initialize the Dash app
app = DjangoDash("ReportApp")


# Fetch default data for initialization
def get_default_columns_and_data():
    default_columns = ["sample_name", "date_acquired", "sample_set_name", "column_name"]
    samples = SampleMetadata.objects.all()  # Fetch all rows
    columns = [{"name": col.replace("_", " ").title(), "id": col} for col in default_columns]
    data = []
    for sample in samples:
        row = {}
        for col in default_columns:
            value = getattr(sample, col, "")
            # Format date_acquired to a readable string format if it's a DateField
            # if col == "date_acquired" and value:
                # value = value.strftime("%Y-%m-%d")  # Format as YYYY-MM-DD
            row[col] = value
        data.append(row)
    return columns, data


# Default columns and data for the table
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
        html.H1(
            "Sample Report Submission",
            style={
                "textAlign": "center",
                "color": "#0047b3",
                "marginBottom": "20px"
            }
        ),

        # Filters Section
        html.Div(
            style={"marginBottom": "20px"},
            children=[
                html.Label("Filter by Sample Type:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="sample_type_filter",
                    options=[
                        {"label": "PD", "value": "PD"},
                        {"label": "UP", "value": "UP"},
                        {"label": "FB", "value": "FB"}
                    ],
                    placeholder="Select sample type",
                    multi=True,
                    style={"marginBottom": "10px"}
                ),

                html.Label("Filter by Sample Set Name:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="sample_set_name_filter",
                    options=[],  # Dynamically populated
                    placeholder="Select sample set name",
                    multi=True,
                    style={"marginBottom": "20px"}
                )
            ]
        ),

        # Column Selection Section
        html.Div(
            style={"marginBottom": "20px"},
            children=[
                html.Label("Select Columns to Display in the Table:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="column_selection",
                    options=[
                        {"label": "Result ID", "value": "result_id"},
                        {"label": "System Name", "value": "system_name"},
                        {"label": "Project Name", "value": "project_name"},
                        {"label": "Sample Prefix", "value": "sample_prefix"},
                        {"label": "Sample Number", "value": "sample_number"},
                        {"label": "Sample Suffix", "value": "sample_suffix"},
                        {"label": "Sample Type", "value": "sample_type"},
                        {"label": "Sample Name", "value": "sample_name"},
                        {"label": "Sample Set ID", "value": "sample_set_id"},
                        {"label": "Sample Set Name", "value": "sample_set_name"},
                        {"label": "Date Acquired", "value": "date_acquired"},
                        {"label": "Acquired By", "value": "acquired_by"},
                        {"label": "Run Time", "value": "run_time"},
                        {"label": "Processing Method", "value": "processing_method"},
                        {"label": "Processed Channel Description", "value": "processed_channel_description"},
                        {"label": "Injection Volume", "value": "injection_volume"},
                        {"label": "Injection ID", "value": "injection_id"},
                        {"label": "Column Name", "value": "column_name"},
                        {"label": "Column Serial Number", "value": "column_serial_number"},
                        {"label": "Instrument Method ID", "value": "instrument_method_id"},
                        {"label": "Instrument Method Name", "value": "instrument_method_name"}
                    ],
                    value=["sample_name", "date_acquired", "sample_set_name", "column_name"],
                    multi=True,
                    placeholder="Select columns to display",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px",
                        "backgroundColor": "white"
                    }
                )
            ]
        ),

        # Data Table Section
        html.Div(
            children=[
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
                    sort_action="native",  # Enable sorting
                    sort_mode="multi",  # Allow multi-column sorting
                    style_table={
                        "overflowX": "auto",
                        "width": "100%",
                        "borderRadius": "5px",
                        "boxShadow": "0px 2px 6px rgba(0, 0, 0, 0.1)"
                    },
                    style_cell={
                        "padding": "10px",
                        "textAlign": "center",
                        "borderBottom": "1px solid #ccc"
                    },
                    style_header={
                        "fontWeight": "bold",
                        "backgroundColor": "#e9f1fb",
                        "color": "#0047b3"
                    },
                    style_data={
                        "backgroundColor": "white",
                        "color": "#333"
                    }
                )
            ],
            style={"marginBottom": "20px"}
        ),

        # Report Details
        html.Div(
            children=[
                html.Label("Report Name:", style={"fontWeight": "bold"}),
                dcc.Input(
                    id="report_name_input",
                    type="text",
                    placeholder="Enter report name",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px"
                    }
                ),
                html.Label("Project ID:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="project_id_dropdown",
                    placeholder="Select or enter a Project ID",
                    options=[],  # Dynamically populated
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px"
                    }
                ),
                dcc.Input(
                    id="new_project_id_input",
                    type="text",
                    placeholder="Enter new Project ID",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px",
                        "display": "none"
                    }
                ),
                html.Label("Comments:", style={"fontWeight": "bold"}),
                dcc.Input(
                    id="comments_input",
                    type="text",
                    placeholder="Enter comments",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px"
                    }
                ),
                html.Label("User ID:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="user_id_dropdown",
                    placeholder="Select or enter a User ID",
                    options=[],  # Dynamically populated
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px"
                    }
                ),
                dcc.Input(
                    id="new_user_id_input",
                    type="text",
                    placeholder="Enter new User ID",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px",
                        "display": "none"
                    }
                )
            ]
        ),

        # Submit Button
        html.Button(
            "Submit Report",
            id="submit_button",
            n_clicks=0,
            style={
                "backgroundColor": "#0047b3",
                "color": "white",
                "padding": "10px 20px",
                "border": "none",
                "borderRadius": "5px",
                "cursor": "pointer",
                "display": "block",
                "margin": "0 auto",
                "marginBottom": "20px"
            }
        ),

        # Submission Status
        html.Div(
            id="submission_status",
            style={
                "textAlign": "center",
                "color": "green",
                "fontWeight": "bold",
                "fontSize": "16px"
            }
        )
    ]
)


# Dynamically update table data based on filters
@app.callback(
    [Output("sample_table", "columns"),
     Output("sample_table", "data")],
    [Input("sample_type_filter", "value"),
     Input("sample_set_name_filter", "value"),
     Input("column_selection", "value")]
)
def update_table(sample_types, sample_set_names, selected_columns):
    # Default columns
    if not selected_columns:
        selected_columns = ["sample_name", "date_acquired", "sample_set_name", "column_name"]

    columns = [{"name": col.replace("_", " ").title(), "id": col} for col in selected_columns]

    # Filter data
    query = SampleMetadata.objects.all()
    if sample_types:
        query = query.filter(sample_prefix__in=sample_types)
    if sample_set_names:
        query = query.filter(sample_set_name__in=sample_set_names)

    data = []
    for sample in query:
        row = {col: getattr(sample, col, "") for col in selected_columns}
        if "date_acquired" in row and row["date_acquired"]:
            if isinstance(row["date_acquired"], str):
                pass  # Already a string, no need to convert
            elif row["date_acquired"]:
                row["date_acquired"] = row["date_acquired"].strftime("%Y-%m-%d")
            else:
                row["date_acquired"] = ""
        data.append(row)

    return columns, data


# Dynamically populate Sample Set Name options based on Sample Type
@app.callback(
    Output("sample_set_name_filter", "options"),
    Input("sample_type_filter", "value")
)
def update_sample_set_options(sample_types):
    query = SampleMetadata.objects.all()
    if sample_types:
        query = query.filter(sample_prefix__in=sample_types)

    sample_set_names = list(query.values_list("sample_set_name", flat=True).distinct())

    # Extract the date prefix (YYMMDD) and convert to datetime for sorting
    def extract_date(sample_set):
        try:
            date_part = sample_set[:6]  # Get first 6 characters
            return datetime.strptime(date_part, "%y%m%d")  # Convert to YYYY-MM-DD format
        except ValueError:
            return datetime.min  # Assign the earliest date if invalid format

    # Sort sample sets by extracted date in descending order (most recent first)
    sample_set_names_sorted = sorted(sample_set_names, key=extract_date, reverse=True)

    return [{"label": name, "value": name} for name in sample_set_names_sorted if name]


# Select All Button
@app.callback(
    Output("sample_table", "selected_rows"),
    Input("select_all_button", "n_clicks"),
    State("sample_table", "data")
)
def select_all_rows(n_clicks, data):
    if n_clicks % 2 == 1:
        return list(range(len(data)))  # Select all rows
    return []  # Deselect all rows


# Callbacks

# Populate Project ID options and toggle new Project ID input
@app.callback(
    [Output("project_id_dropdown", "options"),
     Output("new_project_id_input", "style")],
    [Input("project_id_dropdown", "value")]
)
def populate_project_ids(selected_project_id):
    project_ids = Report.objects.values_list("project_id", flat=True).distinct()
    options = [{"label": pid, "value": pid} for pid in project_ids if pid]
    options.append({"label": "Enter New Project ID", "value": "new_project_id"})

    if selected_project_id == "new_project_id":
        return options, {"display": "block"}
    return options, {"display": "none"}


# Populate User ID options and toggle new User ID input
@app.callback(
    [Output("user_id_dropdown", "options"),
     Output("new_user_id_input", "style")],
    [Input("user_id_dropdown", "value")]
)
def populate_user_ids(selected_user_id):
    user_ids = Report.objects.values_list("user_id", flat=True).distinct()
    options = [{"label": uid, "value": uid} for uid in user_ids if uid]
    options.append({"label": "Enter New User ID", "value": "new_user_id"})

    if selected_user_id == "new_user_id":
        return options, {"display": "block"}
    return options, {"display": "none"}


# Submit Report
@app.callback(
    Output("submission_status", "children"),
    Input("submit_button", "n_clicks"),
    [
        State("report_name_input", "value"),
        State("project_id_dropdown", "value"),
        State("new_project_id_input", "value"),
        State("user_id_dropdown", "value"),
        State("new_user_id_input", "value"),
        State("comments_input", "value"),
        State("sample_table", "data"),
        State("sample_table", "selected_rows")
    ]
)
def submit_report(n_clicks, report_name, project_id, new_project_id, user_id, new_user_id, comments, table_data, selected_rows):
    if n_clicks > 0:
        # Ensure required fields are provided
        if not report_name or (not project_id and not new_project_id) or (not user_id and not new_user_id):
            return "Please provide all required fields."

        # Resolve final Project ID
        final_project_id = new_project_id if project_id == "new_project_id" else project_id

        # Resolve final User ID
        final_user_id = new_user_id if user_id == "new_user_id" else user_id

        # Build selected samples by querying the database for sample_prefix and sample_number
        selected_samples = []
        for i in selected_rows:
            sample_name = table_data[i].get("sample_name", "")
            if sample_name:
                selected_samples.append(sample_name)

        if not selected_samples:
            return "No rows selected. Please select rows to include in the report."

        # **Sort the selected samples**
        selected_samples.sort()  # Sorting the list in ascending order

        # Save the report to the database
        Report.objects.create(
            report_name=report_name,
            project_id=final_project_id,
            user_id=final_user_id,
            comments=comments,
            selected_samples=",".join(selected_samples)  # Join sorted sample names
        )

        return f"Report '{report_name}' created successfully with sorted samples!"

    return "No action performed."

