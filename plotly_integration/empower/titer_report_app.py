import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django_plotly_dash import DjangoDash
import dash
from dash import dcc, html, Input, Output, State, dash_table, Dash, MATCH, callback_context
import pandas as pd
from scipy.stats import linregress, t
from plotly_integration.models import Report, SampleMetadata, PeakResults, TimeSeriesData
import json
import logging
from openpyxl.workbook import Workbook
from collections import Counter
from django.db.models import F, ExpressionWrapper, fields
from datetime import datetime
import re
import numpy as np
from collections import Counter

# Logging Configuration
logging.basicConfig(filename='app_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Dash app
app = DjangoDash('TiterReportApp')


def parse_date(date_value):
    """Convert date strings to datetime objects, return None if invalid."""
    if isinstance(date_value, datetime):
        return date_value
    elif isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value)  # Handle ISO date strings
        except ValueError:
            return None
    return None


# ✅ Fix `fetch_reports()` to handle string dates
def fetch_reports():
    projects = {}
    # ✅ Filter only reports with analysis_type = 2
    filtered_reports = Report.objects.filter(analysis_type=2).values(
        'project_id',
        'report_id',
        'report_name',
        'user_id',
        'selected_samples',
        'date_created'
    )
    for report in filtered_reports:
        if report['project_id'] not in projects:
            projects[report['project_id']] = []
        projects[report['project_id']].append({
            'report_id': report['report_id'],
            'name': report['report_name'],
            'user_id': report.get('user_id', 'N/A'),  # Show N/A if missing
            'selected_samples': report.get('selected_samples', 'None'),  # Default to 'None'
            'date_created': parse_date(report['date_created']).isoformat() if parse_date(
                report['date_created']) else None  # ✅ Convert string to datetime first
        })
    return projects


# Store the initial reports in `dcc.Store` when the app loads
initial_projects = fetch_reports()


def extract_numeric_part(project_id):
    """Extract the first two numeric parts from a project ID (e.g., SI-02x10 -> 2)."""
    match = re.search(r"SI-(\d+)", project_id)
    return int(match.group(1)) if match else float('inf')


def generate_sidebar(projects):
    """Generate a sorted sidebar with projects and their reports."""
    sidebar_items = [
        html.Div("Projects", style={
            'text-align': 'center',
            'margin-bottom': '20px',
            'font-weight': 'bold',
            'font-size': '18px',
            'color': '#003366',
            'padding': '10px',
            'border-bottom': '2px solid #0056b3',
        }),
        # 🔵 Refresh Button
        html.Button(
            "Refresh Project Reports",
            id="refresh-sidebar-btn",
            n_clicks=0,
            style={
                'width': '100%',
                'background-color': '#0056b3',
                'color': 'white',
                'border': 'none',
                'padding': '10px',
                'font-size': '14px',
                'cursor': 'pointer',
                'border-radius': '5px',
                'margin-bottom': '10px',
                'transition': 'all 0.2s ease-in-out'
            }
        ),
    ]

    # ✅ Sort projects by numeric part (e.g., SI-01, SI-02)
    sorted_projects = sorted(projects.items(), key=lambda x: extract_numeric_part(x[0]))

    for project_id, reports in sorted_projects:
        # ✅ Sort reports by `date_created` (most recent first) with proper parsing
        sorted_reports = sorted(
            reports,
            key=lambda r: parse_date(r.get('date_created')) or datetime.min,
            reverse=True  # ✅ Newest first
        )

        project_folder = html.Div([
            html.Div(
                f"📁 {project_id}",
                className="folder",
                id={'type': 'folder', 'project_id': project_id},
                n_clicks=0,
                style={
                    'cursor': 'pointer',
                    'margin-bottom': '10px',
                    'font-weight': 'bold',
                    'color': '#0056b3',
                    'padding': '10px',
                    'border': '1px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#e0f0ff',
                },
            ),
            html.Div(
                [
                    html.Div([
                        html.Div(f"📄 {report['name']}", style={
                            'font-weight': 'bold',
                            'color': '#003366',
                            'margin-bottom': '5px',
                        }),
                        html.Div(
                            # ✅ Show actual `date_created` or "N/A"
                            f"Date Created: {parse_date(report.get('date_created')).strftime('%Y-%m-%d %H:%M:%S') if parse_date(report.get('date_created')) else 'N/A'}",
                            style={
                                'font-size': '12px',
                                'color': '#555',
                                'margin-left': '10px',
                            },
                        ),
                        html.Div(
                            # ✅ Show actual `date_created` or "N/A"
                            f"Created By: {report['user_id']}",
                            style={
                                'font-size': '12px',
                                'color': '#555',
                                'margin-left': '10px',
                            },
                        ),
                        html.Div(
                            # ✅ Show actual `date_created` or "N/A"
                            f"Selected Samples: {report['selected_samples']}",
                            style={
                                'font-size': '12px',
                                'color': '#555',
                                'margin-left': '10px',
                            },
                        ),
                        html.Div(
                            # ✅ Show actual `date_created` or "N/A"
                            f"Report ID: {report['report_id']}",
                            style={
                                'font-size': '12px',
                                'color': '#555',
                                'margin-left': '10px',
                            },
                        ),
                    ],
                        className="report",
                        id={'type': 'report', 'report_name': report['report_id']},
                        style={
                            'border': '1px solid #ccc',
                            'padding': '10px',
                            'margin-bottom': '5px',
                            'background-color': '#f9f9f9',
                            'border-radius': '5px',
                        },
                    )
                    for report in sorted_reports
                ],
                className="folder-contents",
                style={'display': 'none', 'margin-left': '10px'},
                id={'type': 'contents', 'project_id': project_id}
            )
        ])
        sidebar_items.append(project_folder)

    return sidebar_items


# Layout for the Dash app
app.layout = html.Div([

    dcc.Store(id='selected-report', data=None),
    dcc.Store(id="std-result-id-store"),
    dcc.Store(id='regression-parameters', data={"slope": 0,
                                                "intercept": 0,
                                                "std_err": 0,
                                                "t_score": 0,
                                                "n": 0,
                                                "mean_x": 0,
                                                "sum_x_sq": 0
                                                }),
    dcc.Store(id='result-table-store', data=[]),
    dcc.Store(id='report-list-store', data=[]),

    # 🔹 Top-left Home Button
    html.Div(
        html.Button("Home", id="home-btn", style={
            'background-color': '#0056b3',
            'color': 'white',
            'border': 'none',
            'padding': '10px 20px',
            'font-size': '16px',
            'cursor': 'pointer',
            'border-radius': '5px'
        }),
        style={'margin': '10px'}
    ),

    html.Div([  # Main layout with sidebar and content areas
        html.Div(  # Sidebar
            id='sidebar',
            children=generate_sidebar(initial_projects),
            style={
                'width': '20%',
                'height': 'calc(100vh - 50px)',
                'background-color': '#f7f7f7',
                'padding': '10px',
                'overflow-y': 'auto',
                'border': '2px solid #0056b3',
                'border-radius': '5px',
                'flex-shrink': '0'
            }
        ),

        html.Div([  # Main content container
            dcc.Tabs(id="main-tabs", value="tab-1", children=[

                # 🔹 Tab 1: Sample Analysis
                dcc.Tab(label="Sample Analysis", value="tab-1", children=[
                    html.Div([
                        html.Div(  # Plot area (90% width)
                            id='plot-area',
                            children=[
                                html.H4("Titer Results", id="results-header",
                                        style={'text-align': 'center', 'color': '#0056b3'}),
                                dcc.Graph(id='time-series-graph')
                            ],
                            style={
                                'width': '98%',  # ✅ Increased width to 90%
                                'margin': 'auto',
                                'padding': '10px',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                                'background-color': '#f7f9fc',
                                'margin-bottom': '10px'
                            }
                        ),

                        html.Div(  # ✅ Plot settings moved below plot
                            id='plot-settings',
                            children=[
                                html.H4("Plot Settings", style={'color': '#0056b3', 'text-align': 'center'}),
                                dcc.RadioItems(  # ✅ Horizontal layout for radio buttons
                                    id='channel-radio',
                                    options=[
                                        {'label': 'UV280', 'value': 'channel_1'},
                                        {'label': 'UV260', 'value': 'channel_2'},
                                        {'label': 'Pressure', 'value': 'channel_3'}
                                    ],
                                    value='channel_1',  # Default selection
                                    labelStyle={'display': 'inline-block', 'margin-right': '15px'}
                                    # ✅ Horizontal layout
                                ),
                                dcc.Dropdown(
                                    id='plot-type-dropdown',
                                    options=[
                                        {'label': 'Plotly Graph', 'value': 'plotly'},
                                        {'label': 'Subplots', 'value': 'subplots'}
                                    ],
                                    value='plotly',
                                    style={'width': '100%', 'margin-top': '10px'}
                                ),
                            ],
                            style={
                                'width': '98%',  # ✅ Increased width to 90%
                                'margin': 'auto',
                                'padding': '10px',
                                'background-color': '#f7f9fc',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                                'margin-bottom': '10px'
                            }
                        ),

                        html.Div(  # Titer Data Table
                            id='titer-data',
                            children=[
                                html.H4("Titer Results", style={'text-align': 'center', 'color': '#0056b3'}),
                                dash_table.DataTable(
                                    id='result-table',
                                    columns=[
                                        {"name": "Sample Name", "id": "Sample Name"},
                                        {"name": "Dilution Factor", "id": "Dilution Factor"},
                                        {"name": "Peak Start", "id": "Peak Start"},
                                        {"name": "Peak End", "id": "Peak End"},
                                        {"name": "Main Peak Area", "id": "Main Peak Area"},
                                        {"name": "Concentration (mg/mL)", "id": "Concentration"},
                                        {"name": "Uncertainty", "id": "Uncertainty"},
                                        {"name": "Injection Volume (uL)", "id": "Injection Volume"}
                                    ],
                                    data=[],
                                    # row_selectable="single",  # ✅ Changed to single row selection
                                    # selected_rows=[],
                                    sort_action="native",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'center', 'padding': '5px'},
                                    style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                                ),
                                html.Button("Export to XLSX", id="export-button", style={  # ✅ Added back export button
                                    'margin-top': '10px',
                                    'background-color': '#0047b3',
                                    'color': 'white',
                                    'padding': '10px',
                                    'border': 'none',
                                    'border-radius': '5px',
                                    'cursor': 'pointer'
                                }),
                                dcc.Download(id="download-result-data")
                            ],
                            style={
                                'width': '98%',  # ✅ Increased width to 90%
                                'margin': 'auto',
                                'padding': '10px',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                                'background-color': '#f7f9fc'
                            }
                        ),
                    ])
                ]),
                # 🔹 Tab 2: Standard Analysis
                dcc.Tab(label="Standard Analysis", value="tab-2", children=[
                    html.Div(
                        id='standard-analysis',
                        children=[
                            html.H4("Standard Analysis", style={'text-align': 'center', 'color': '#0056b3'}),
                            dcc.Graph(id='standard-plot', style={'margin-top': '10px'}),

                            html.Div(
                                id='standard-analysis-content',
                                children=[
                                    dcc.Graph(id='regression-plot', style={'margin-top': '20px'}),
                                    dash_table.DataTable(
                                        id="standard-table",
                                        columns=[
                                            {"name": "Sample Name", "id": "Sample Name"},
                                            {"name": "Peak Start", "id": "Peak Start"},
                                            {"name": "Peak End", "id": "Peak End"},
                                            {"name": "Peak Area", "id": "Main Peak Area"},
                                            {"name": "Concentration (mg/mL)", "id": "Concentration (mg/mL)"},
                                            {"name": "Injection Volume (uL)", "id": "Injection Volume (uL)"}
                                        ],
                                        data=[],
                                        row_selectable='multi',
                                        selected_rows=[],
                                        style_table={'overflowX': 'auto'},
                                        style_cell={'textAlign': 'center', 'padding': '5px'},
                                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                                    )
                                ],
                                style={
                                    'padding': '10px',
                                    'border': '2px solid #0056b3',
                                    'border-radius': '5px',
                                    'background-color': '#f7f9fc',
                                }
                            ),

                            html.P("Regression Equation: ", id="regression-equation"),
                            html.P("R² Value: ", id="r-squared-value"),
                        ],
                        style={
                            'width': '95%',
                            'margin-top': '20px',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc'
                        }
                    )
                ])
            ])
        ], style={'width': '95%', 'padding': '10px', 'overflow-y': 'auto'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'})
])


@app.callback(
    Output("results-header", "children"),  # Update the SEC Results header
    [Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def update_results_header(report_clicks):
    ctx = dash.callback_context  # Correctly access callback context

    if not ctx.triggered:
        return "Titer Results"

    # Extract triggered report name
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        triggered_data = eval(triggered_id)  # Convert string ID to dictionary
    except Exception:
        return "Error: Invalid Report Data"

    if 'report_name' not in triggered_data:
        return "Titer Results"

    report_name = triggered_data['report_name']
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        return "Report Not Found"

    # Format the SEC Results text
    return f"{report.project_id} - {report.report_name}"


# Sidebar Logic
@app.callback(
    Output({'type': 'contents', 'project_id': MATCH}, 'style'),
    Input({'type': 'folder', 'project_id': MATCH}, 'n_clicks'),
    prevent_initial_call=True
)
def toggle_folder(n_clicks):
    """
    Toggle the visibility of a specific folder based on click count.
    """
    if not n_clicks:
        return dash.no_update  # Prevent unnecessary updates

    # Toggle visibility only for the clicked folder
    return {'display': 'block'} if n_clicks % 2 != 0 else {'display': 'none'}


@app.callback(
    Output('sidebar', 'children'),
    Input('refresh-sidebar-btn', 'n_clicks')
)
def refresh_sidebar(n_clicks):
    if n_clicks == 0:
        raise dash.exceptions.PreventUpdate

    # ✅ Fetch reports from the Report table with `date_created`
    projects = fetch_reports()

    return generate_sidebar(projects)


@app.callback(
    Output("sample-details-table", "data"),
    Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_sample_and_std_details(report_clicks):
    ctx = dash.callback_context

    # Default table data
    default_data = [
        {"field": "Sample Set Name", "value": ""},
        {"field": "Column Name", "value": ""},
        {"field": "Column Serial Number", "value": ""},
        {"field": "System Name", "value": ""},
        {"field": "Instrument Method Name", "value": ""},
    ]

    if not ctx.triggered:
        return default_data

    # Determine the triggering report
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_data = eval(triggered_id)

    if 'report_name' not in triggered_data:
        return default_data

    report_name = triggered_data['report_name']
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        return default_data

    # Fetch the first sample name from the report's selected samples
    selected_result_ids = [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()]
    if not selected_result_ids:
        return default_data

    first_sample_name = selected_result_ids[0]
    sample_metadata = SampleMetadata.objects.filter(result_id=first_sample_name).first()

    if not sample_metadata:
        return default_data

    # Extract details from the `SampleMetadata` model
    sample_set_name = sample_metadata.sample_set_name or "N/A"
    column_name = sample_metadata.column_name or "N/A"
    column_serial_number = sample_metadata.column_serial_number or "N/A"
    system_name = sample_metadata.system_name or "N/A"
    instrument_method_name = sample_metadata.instrument_method_name or "N/A"

    # Return table data
    return [
        {"field": "Sample Set Name", "value": sample_set_name},
        {"field": "Column Name", "value": column_name},
        {"field": "Column Serial Number", "value": column_serial_number},
        {"field": "System Name", "value": system_name},
        {"field": "Instrument Method Name", "value": instrument_method_name},
    ]


def extract_concentration(sample_name):
    """Extracts concentration from sample names formatted as '130E7 Std_x'."""
    match = re.search(r"Std_([\d\.]+)", sample_name)
    return float(match.group(1)) if match else None


@app.callback(
    Output("standard-plot", "figure"),  # ✅ Time series data for standards
    [
        Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks')  # ✅ Trigger on report click
    ],
    [State("selected-report", "data")],  # ✅ Use the stored selected report
    prevent_initial_call=True
)
def plot_standard_time_series(report_clicks, selected_report):
    """Fetch time series data for standard samples in the selected report and plot it."""

    ctx = dash.callback_context

    # ✅ Determine the triggering input
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_data = json.loads(triggered_id.replace("'", '"'))
    except json.JSONDecodeError:
        triggered_data = {}

    # ✅ Ensure `report_name` is valid
    report_name = selected_report
    if 'report_name' in triggered_data:
        report_name = triggered_data['report_name']  # **New report clicked**
    elif isinstance(selected_report, str) and selected_report:  # **Ensure stored report is valid**
        report_name = selected_report

    if not report_name:
        print("🚨 No report selected.")
        return go.Figure()

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        print(f"🚨 Report not found: {report_name}")
        return go.Figure()

    # ✅ Extract standard samples from the selected report
    selected_samples = [s.strip() for s in report.selected_samples.split(",") if s.strip()]

    if not selected_samples:
        print(f"🚨 No samples found in report: {report_name}")
        return go.Figure()

    print(f"✅ Selected Report: {report_name}")
    print(f"📢 Found Samples: {selected_samples}")

    # ✅ Retrieve standard samples (`Std_`) that belong to this report
    std_samples = SampleMetadata.objects.filter(
        sample_name__in=selected_samples,  # 🔥 Only include samples from the report
        sample_name__contains="Std_"  # 🔥 Only include standards
    ).values("sample_name", "result_id")

    if not std_samples:
        print(f"🚨 No standard samples found in report: {report_name}")
        return go.Figure()

    print(f"✅ Found Standard Samples: {[s['sample_name'] for s in std_samples]}")

    # ✅ Initialize Plotly Figure
    fig = go.Figure()

    # ✅ Retrieve Time Series Data for Each Standard Sample
    for std in std_samples:
        result_id = std["result_id"]
        sample_name = std["sample_name"]

        # ✅ Fetch Time Series Data from `TimeSeriesData`
        time_series = TimeSeriesData.objects.filter(result_id=result_id).values("time", "channel_1")

        df = pd.DataFrame(list(time_series))  # Convert to DataFrame

        if df.empty:
            print(f"⚠️ No Time Series Data for: {sample_name}")
            continue

        # ✅ Add Trace to the Plot
        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df["channel_1"],
            mode="lines",
            name=sample_name
        ))

    # ✅ Update Plot Layout
    fig.update_layout(
        title="Time Series Data for Standards",
        xaxis_title="Time",
        yaxis_title="Signal Intensity",
        template="plotly_white"
    )

    return fig


@app.callback(
    [
        Output("standard-table", "data"),  # ✅ Populate the table
        Output("standard-table", "selected_rows")  # ✅ Default: Select first 5 rows
    ],
    [
        Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks')  # ✅ Trigger on report selection
    ],
    [State("selected-report", "data")],  # ✅ Use stored selected report
    prevent_initial_call=True
)
def update_standard_table(report_clicks, selected_report):
    """Populate standard-table when a report is selected, and set default selected rows."""

    ctx = dash.callback_context

    # ✅ Preserve report selection
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_data = json.loads(triggered_id.replace("'", '"'))
    except json.JSONDecodeError:
        triggered_data = {}

    report_name = selected_report
    if 'report_name' in triggered_data:
        report_name = triggered_data['report_name']
    elif isinstance(selected_report, str) and selected_report:
        report_name = selected_report

    if not report_name:
        return [], []

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()
    if not report:
        return [], []

    # ✅ Extract standard samples from the selected report
    all_samples = [s.strip() for s in report.selected_samples.split(",") if s.strip()]
    std_samples = SampleMetadata.objects.filter(
        sample_name__in=all_samples,
        sample_name__contains="Std_"
    ).values("sample_name", "injection_volume", "result_id")

    if not std_samples:
        return [], []

    table_data = []
    for std in std_samples:
        concentration = extract_concentration(std["sample_name"])
        injection_volume = std["injection_volume"]
        result_id = std["result_id"]

        # ✅ Fetch Peak Area, Peak Start, and Peak End from PeakResults Table
        peak_result = PeakResults.objects.filter(result_id=result_id).values("area", "peak_start_time",
                                                                             "peak_end_time").first()
        peak_area = peak_result["area"] if peak_result else None
        peak_start = peak_result["peak_start_time"] if peak_result else None
        peak_end = peak_result["peak_end_time"] if peak_result else None

        if concentration and peak_area:
            table_data.append({
                "Sample Name": std["sample_name"],
                "Peak Start": peak_start,
                "Peak End": peak_end,
                "Main Peak Area": peak_area,
                "Concentration (mg/mL)": concentration,
                "Injection Volume (uL)": injection_volume
            })

    # ✅ Sort table by concentration (lowest to highest)
    table_data = sorted(table_data, key=lambda x: x["Concentration (mg/mL)"])

    # ✅ Select all rows by default
    selected_rows = list(range(len(table_data)))  # ✅ Select all rows

    return table_data, selected_rows


@app.callback(
    [
        Output("regression-equation", "children"),
        Output("r-squared-value", "children"),
        Output("regression-plot", "figure"),  # ✅ Regression Plot
        Output("regression-parameters", "data")  # Store slope & intercept for calculations
    ],
    [
        Input("standard-table", "selected_rows")  # ✅ Trigger on row selection
    ],
    [
        State("standard-table", "data")  # ✅ Use existing table data
    ],
    prevent_initial_call=True
)
def update_regression_plot(selected_rows, table_data):
    """Update regression plot based on selected rows from the standard-table."""

    if not table_data or not selected_rows:
        return "No Standard Data Selected", "N/A", go.Figure(), {"slope": None, "intercept": None}

    # ✅ Filter selected rows
    selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
    selected_df = pd.DataFrame(selected_data)

    if selected_df.empty:
        return "No Standard Data Selected", "N/A", go.Figure(), {"slope": None, "intercept": None}

    # ✅ Extract x (concentration) and y (peak area)
    concentrations = selected_df["Concentration (mg/mL)"].astype(float)
    peak_areas = selected_df["Main Peak Area"].astype(float)

    # ✅ Perform Linear Regression
    try:
        slope, intercept, r_value, _, std_err = linregress(concentrations, peak_areas)  # ✅ std_err = standard deviation
    except Exception as e:
        print(f"Regression error: {e}")
        return "Regression Failed", "N/A", go.Figure(), {"slope": None, "intercept": None, "std_dev": None}

    # ✅ Generate Regression Line
    x_vals = np.linspace(concentrations.min(), concentrations.max(), 100)
    y_vals = slope * x_vals + intercept

    # ✅ Compute Prediction Interval

    n = len(concentrations)  # Number of data points
    mean_x = np.mean(concentrations)
    sum_x_sq = np.sum((concentrations - mean_x) ** 2)

    # ✅ t-score for 95% confidence
    t_score = t.ppf(0.975, df=n - 2)  # Two-tailed 95% confidence

    print(std_err)
    print(n)
    print(mean_x)
    print(sum_x_sq)

    # ✅ Create Plotly Figure for Regression
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=concentrations,
        y=peak_areas,
        mode="markers",
        name="Standard Data",
        marker=dict(size=8, color="blue")
    ))
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        name="Regression Line",
        line=dict(color="red", dash="dash")
    ))

    # ✅ Add annotations for each data point
    for i, (x, y) in enumerate(zip(concentrations, peak_areas)):
        fig.add_annotation(
            x=x, y=y,
            text=f"{x:.3f} mg/mL",
            showarrow=True,
            arrowhead=2,
            ax=0, ay=-20
        )

    fig.update_layout(
        title="Regression Analysis: Concentration vs Peak Area",
        xaxis_title="Concentration (mg/mL)",
        yaxis_title="Peak Area",
        template="plotly_white"
    )

    return (
        f"y = {slope:.4f}x + {intercept:.4f}",
        f"R² = {r_value ** 2:.4f}",
        fig,  # ✅ Regression plot updates dynamically
        {"slope": slope,
         "intercept": intercept,
         "std_err": std_err,
         "t_score": t_score,
         "n": n,
         "mean_x": mean_x,
         "sum_x_sq": sum_x_sq
         }
    )


@app.callback(
    [
        Output("result-table", "columns"),  # ✅ Table column structure
        Output("result-table", "data"),  # ✅ Populate the result table
        Output("selected-report", "data")  # ✅ Preserve selected report
    ],
    [
        Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),  # ✅ Trigger on report selection
        Input("regression-parameters", "data")  # ✅ Trigger when regression parameters change
    ],
    [State("selected-report", "data")],  # ✅ Use stored selected report
    prevent_initial_call=True
)
def update_result_table(report_clicks, regression_params, selected_report):
    """Populate result-table with all report samples and update calculated concentrations using regression parameters."""

    ctx = dash.callback_context

    # ✅ Determine which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_data = json.loads(triggered_id.replace("'", '"'))
    except json.JSONDecodeError:
        triggered_data = {}

    # ✅ Preserve report selection when regression parameters change
    report_name = selected_report
    if 'report_name' in triggered_data:
        report_name = triggered_data['report_name']
    elif isinstance(selected_report, str) and selected_report:
        report_name = selected_report

    if not report_name:
        print("⚠️ No report found or selected. Returning empty table.")
        return [], [], None

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()
    if not report:
        print(f"⚠️ Report '{report_name}' not found in database.")
        return [], [], report_name

    # ✅ Extract all samples from the report
    all_samples = [s.strip() for s in report.selected_samples.split(",") if s.strip()]
    report_samples = SampleMetadata.objects.filter(sample_name__in=all_samples).values(
        "sample_name", "injection_volume", "result_id"
    )

    if not report_samples:
        print(f"⚠️ No samples found in report '{report_name}'.")
        return [], [], report_name

    # ✅ Extract regression parameters
    slope = regression_params.get("slope")
    intercept = regression_params.get("intercept")
    std_err = regression_params.get("std_err")
    t_score = regression_params.get("t_score")
    n = regression_params.get("n")
    mean_x = regression_params.get("mean_x")
    sum_x_sq = regression_params.get("sum_x_sq")

    # ✅ Initialize result data list
    result_data = []

    for i, sample in enumerate(report_samples):
        sample_name = sample["sample_name"]
        injection_volume = sample["injection_volume"]
        result_id = sample["result_id"]

        # Retrieve the SampleMetadata instance for the given result_id
        sample_metadata = SampleMetadata.objects.filter(result_id=result_id).first()

        # Check if the instance exists and retrieve dilution, default to 1 if None
        dilution_factor = sample_metadata.dilution if sample_metadata and sample_metadata.dilution is not None else 1

        print(dilution_factor)  # ✅ Check the output

        # ✅ Fetch Peak Area, Peak Start, and Peak End from PeakResults Table
        peak_result = PeakResults.objects.filter(result_id=result_id).values("area", "peak_start_time",
                                                                             "peak_end_time").first()
        peak_area = peak_result["area"] if peak_result else None
        peak_start = peak_result["peak_start_time"] if peak_result else None
        peak_end = peak_result["peak_end_time"] if peak_result else None

        # ✅ Calculate concentration using regression parameters (if available)
        calculated_concentration = None
        uncertainty = None  # Prediction interval uncertainty

        if peak_area and slope is not None and intercept is not None:
            calculated_concentration = round(((peak_area - intercept) / slope) * dilution_factor, 3) if slope else None

            # ✅ Compute uncertainty using the prediction interval
            if calculated_concentration is not None and slope is not None and intercept is not None:
                # Use the correct prediction interval equation
                uncertainty = t_score * std_err * np.sqrt(
                    1 + (1 / n) + ((calculated_concentration - mean_x) ** 2 / sum_x_sq))

                # Convert peak area uncertainty into concentration uncertainty
                uncertainty /= abs(slope)  # ✅ Divide by the absolute slope

                # ✅ Round values for better display
                calculated_concentration = round(calculated_concentration, 3)
                uncertainty = round(uncertainty, 3)

        # ✅ Append sample to results table
        result_data.append({
            "Sample Name": sample_name,
            "Dilution Factor": dilution_factor,
            "Peak Start": peak_start,
            "Peak End": peak_end,
            "Main Peak Area": peak_area,
            "Concentration (mg/mL)": calculated_concentration,
            "Uncertainty": f"{calculated_concentration:.3f} ± {uncertainty:.3f}" if calculated_concentration and uncertainty else None,
            "Injection Volume (uL)": injection_volume,
            "Result ID": result_id  # ✅ Store `Result ID` for sorting later
        })

    # ✅ Sort non-Std_ samples by `Result ID`, keeping `Std_` samples at the end
    result_data_sorted = sorted(
        result_data,
        key=lambda x: ("Std_" in x["Sample Name"], x["Result ID"])
    )

    # ✅ Define table columns dynamically
    table_columns = [
        {"name": "Sample Name", "id": "Sample Name"},
        {"name": "Peak Start", "id": "Peak Start"},
        {"name": "Peak End", "id": "Peak End"},
        {"name": "Main Peak Area", "id": "Main Peak Area"},
        {"name": "Concentration (mg/mL)", "id": "Concentration (mg/mL)"},
        {"name": "Uncertainty", "id": "Uncertainty"},
        {"name": "Injection Volume (uL)", "id": "Injection Volume (uL)"},
    ]

    return table_columns, result_data_sorted, report_name


@app.callback(
    [Output("download-result-data", "data")],
    [
        Input("export-button", "n_clicks"),
    ],
    [
        State("result-table", "data"),
        State('selected-report', 'data')
    ],  # Use the stored selected report
    prevent_initial_call=True
)
def export_to_xlsx(n_clicks, table_data, selected_report):
    if not table_data:
        return dash.no_update  # Do nothing if the table is empty

    print(selected_report)
    # Fetch report details from the database
    report = Report.objects.filter(report_id=int(selected_report)).first()
    print(report)
    print(report.project_id)
    print(report.report_name)

    if not report:
        return dash.no_update

    # Get current date
    current_date = datetime.now().strftime("%Y%m%d")

    # Build the file name
    file_name = f"{current_date}-{report.project_id}-{report.report_name}.xlsx"
    print(file_name)

    # Convert table data to a pandas DataFrame
    df = pd.DataFrame(table_data)

    # Use Dash's `send_data_frame` to export the DataFrame as an XLSX file
    return [dcc.send_data_frame(df.to_excel, file_name, index=False)]


@app.callback(
    Output("time-series-graph", "figure"),  # ✅ Time series data for standards
    [
        Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks')  # ✅ Trigger on report click
    ],
    [State("selected-report", "data")],  # ✅ Use the stored selected report
    prevent_initial_call=True
)
def plot_standard_time_series(report_clicks, selected_report):
    """Fetch time series data for standard samples in the selected report and plot it."""

    ctx = dash.callback_context

    # ✅ Determine the triggering input
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_data = json.loads(triggered_id.replace("'", '"'))
    except json.JSONDecodeError:
        triggered_data = {}

    # ✅ Ensure `report_name` is valid
    report_name = selected_report
    if 'report_name' in triggered_data:
        report_name = triggered_data['report_name']  # **New report clicked**
    elif isinstance(selected_report, str) and selected_report:  # **Ensure stored report is valid**
        report_name = selected_report

    if not report_name:
        print("🚨 No report selected.")
        return go.Figure()

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        print(f"🚨 Report not found: {report_name}")
        return go.Figure()

    # ✅ Extract standard samples from the selected report
    selected_samples = [s.strip() for s in report.selected_samples.split(",") if s.strip()]

    if not selected_samples:
        print(f"🚨 No samples found in report: {report_name}")
        return go.Figure()

    print(f"✅ Selected Report: {report_name}")
    print(f"📢 Found Samples: {selected_samples}")

    # ✅ Retrieve non-standard samples (Exclude "Std_") and sort by result_id
    non_std_samples = SampleMetadata.objects.filter(
        sample_name__in=selected_samples
    ).exclude(sample_name__contains="Std_").order_by("result_id")  # ✅ Sort by result_id

    if not non_std_samples:
        print(f"🚨 No samples found in report: {report_name}")
        return go.Figure()

    print(f"✅ Found Samples: {[s.sample_name for s in non_std_samples]}")

    # ✅ Initialize Plotly Figure
    fig = go.Figure()

    # ✅ Retrieve Time Series Data for Each Standard Sample
    for sample in non_std_samples:
        result_id = sample.result_id  # ✅ Correct way to access model attributes
        sample_name = sample.sample_name

        # ✅ Fetch Time Series Data from `TimeSeriesData`
        time_series = TimeSeriesData.objects.filter(result_id=result_id).values("time", "channel_1")

        df = pd.DataFrame(list(time_series))  # Convert to DataFrame

        if df.empty:
            print(f"⚠️ No Time Series Data for: {sample_name}")
            continue

        # ✅ Add Trace to the Plot
        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df["channel_1"],
            mode="lines",
            name=sample_name
        ))

    # ✅ Update Plot Layout
    fig.update_layout(
        title="Time Series Data for Standards",
        xaxis_title="Time (min)",
        yaxis_title="UV280",
        template="plotly_white"
    )

    return fig
