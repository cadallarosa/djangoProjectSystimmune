import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django_plotly_dash import DjangoDash
import dash
from dash import dcc, html, Input, Output, State, dash_table, Dash
import pandas as pd
from scipy.stats import linregress
from plotly_integration.models import Report, SampleMetadata, PeakResults, TimeSeriesData
import json
import logging
from openpyxl.workbook import Workbook
from django.db.models import F, ExpressionWrapper, fields

# Logging Configuration
logging.basicConfig(filename='app_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Dash app
app = DjangoDash('TimeSeriesApp2')

# Molecular weight mapping
MW_MAPPING = {
    'Peak1-Thyroglobulin': 1400000,
    'Peak2-Thyroglobulin': 660000,
    'Peak3-IgG': 150000,
    'Peak4-BSA': 66400,
    'Peak5-Myoglobin': 17000,
    'Peak6-Uracil': 112
}

# Fetch available projects and reports
projects = {}
for report in Report.objects.all():
    if report.project_id not in projects:
        projects[report.project_id] = []
    projects[report.project_id].append({
        'name': report.report_name, 'samples': report.selected_samples
    })


# Sidebar content generator
def generate_sidebar(projects):
    sidebar_items = [
        html.Div("Projects", style={
            'text-align': 'center',
            'margin-bottom': '10px',
            'font-weight': 'bold',
            'font-size': '14px',
            'color': '#003366',
            'padding': '5px',
            'border-bottom': '1px solid #0056b3',
        }),
        html.P("Hover over a report to see its samples", style={
            'font-size': '10px',
            'color': '#777',
            'text-align': 'center',
            'margin-bottom': '10px',
        }),
    ]

    for project_id, reports in projects.items():
        project_folder = html.Div([
            html.Div(
                f"📁 {project_id}",
                className="folder",
                id={'type': 'folder', 'project_id': project_id},
                n_clicks=0,
                style={
                    'cursor': 'pointer',
                    'margin-bottom': '5px',
                    'font-weight': 'bold',
                    'color': '#0056b3',
                    'padding': '5px',
                    'border': '1px solid #0056b3',
                    'border-radius': '3px',
                    'background-color': '#e0f0ff',
                    'transition': 'all 0.2s ease-in-out',
                    'box-shadow': '0px 1px 2px rgba(0, 0, 0, 0.1)',
                    'font-size': '12px'
                },
            ),
            html.Div(
                [
                    html.Div(
                        f"📄 {report['name']}",
                        className="report",
                        id={'type': 'report', 'report_name': report['name']},
                        **{'data-samples': report['samples']},  # Store samples for hover
                        style={
                            'border': '1px solid #ccc',
                            'padding': '5px',
                            'margin-bottom': '3px',
                            'background-color': '#f9f9f9',
                            'cursor': 'pointer',
                            'border-radius': '3px',
                            'transition': 'all 0.2s ease-in-out',
                            'box-shadow': '0px 1px 2px rgba(0, 0, 0, 0.1)',
                            'font-size': '12px'
                        },
                    ) for report in reports
                ],
                className="folder-contents",
                style={'display': 'none', 'margin-left': '5px'},
                id={'type': 'contents', 'project_id': project_id}
            )
        ])
        sidebar_items.append(project_folder)
    return sidebar_items


# Layout for the Dash app
app.layout = html.Div([
    dcc.Store(id='selected-report', data=None),
    dcc.Store(id="std-result-id-store"),
    dcc.Store(id='regression-parameters', data={'slope': 0, 'intercept': 0}),
    dcc.Store(id='main-peak-rt-store', data=5.10),  # Default value for main peak RT
    dcc.Store(id='low-mw-cutoff-store', data=18),  # Default value for low MW cutoff
    dcc.Store(id='hmw-table-store', data=[]),

    # Top-left Home Button
    html.Div(
        id="selected-report-display",
        style={
            'margin-top': '10px',
            'padding': '10px',
            'border': '1px solid #0056b3',
            'border-radius': '5px',
            'background-color': '#f0f8ff',
            'color': '#003366',
            'font-weight': 'bold',
            'text-align': 'center'
        }
    ),
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
        html.Div(
            id='sidebar',
            children=generate_sidebar(projects),
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
            html.Div(  # Project header
                id='project-header',
                children=[
                    html.H3("Project ID - Analysis Type", style={
                        'margin': '10px',
                        'color': '#0056b3',
                        'text-align': 'center',
                        'border-bottom': '2px solid #0056b3'
                    })
                ],
                style={
                    'width': '68%',
                    'padding': '10px',
                    'border': '2px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#f7f9fc',
                    'margin-bottom': '10px'

                }
            ),
            html.Div([  # Plot and settings
                dcc.Store(id='selected-report', data={}),  # Add this line for state persistence
                html.Div(  # Plot area
                    id='plot-area',
                    children=[
                        html.H4("SEC Results", style={'text-align': 'center', 'color': '#0056b3'}),
                        dcc.Graph(
                            id='time-series-graph',
                            figure=go.Figure(
                                data=[go.Scatter(
                                    x=[],
                                    y=[],
                                    mode='lines'
                                )],
                                layout=go.Layout(
                                    title="Sample Plot",
                                    xaxis_title="Time",
                                    yaxis_title="UV280",
                                    height=800  # Adjust height (default is 400)

                                )
                            )
                        )
                    ],
                    style={
                        'width': '70%',
                        'padding': '10px',
                        'border': '2px solid #0056b3',
                        'border-radius': '5px',
                        'background-color': '#f7f9fc',
                        'margin-bottom': '10px'
                    }
                ),
                html.Div(  # Plot settings
                    id='plot-settings',
                    children=[
                        html.H4("Plot Settings", style={'color': '#0056b3'}),
                        dcc.Checklist(
                            id='channel-checklist',
                            options=[
                                {'label': 'Channel 1', 'value': 'channel_1'},
                                {'label': 'Channel 2', 'value': 'channel_2'},
                                {'label': 'Channel 3', 'value': 'channel_3'}
                            ],
                            value=['channel_1']
                        ),
                        html.Div([
                            html.Label("Select Plot Type:", style={'color': '#0056b3'}),
                            dcc.Dropdown(
                                id='plot-type-dropdown',
                                options=[
                                    {'label': 'Plotly Graph', 'value': 'plotly'},
                                    {'label': 'Subplots', 'value': 'subplots'}
                                ],
                                value='plotly',  # Default value
                                style={'width': '100%'}
                            )
                        ], style={'margin-top': '10px'}),
                        dcc.Checklist(
                            id='shading-checklist',
                            options=[
                                {'label': 'Enable Shading', 'value': 'enable_shading'}
                            ],
                            value=['enable_shading'],  # Default to off
                            style={'margin-top': '10px'}
                        ),
                        html.Div([
                            html.Label("Main Peak RT:", style={'color': '#0056b3'}),
                            dcc.Input(
                                id='main-peak-rt-input',
                                type='number',
                                value=5.10,  # Default value
                                style={'width': '100%'}
                            )
                        ], style={'margin-top': '10px'}),
                        html.Div([
                            html.Label("LMW Cutoff Time:", style={'color': '#0056b3'}),
                            dcc.Input(
                                id='low-mw-cutoff-input',
                                type='number',
                                value=18,  # Default value
                                style={'width': '100%'}
                            )
                        ], style={'margin-top': '10px'}),

                        dcc.Checklist(
                            id='peak-label-checklist',
                            options=[
                                {'label': 'Enable Peak Labeling', 'value': 'enable_peak_labeling'}
                            ],
                            value=['enable_peak_labeling'],  # Default to no peak labeling
                            style={'margin-top': '10px'}
                        )

                    ],
                    style={
                        'height': '30%',
                        'width': '30%',
                        'padding': '10px',
                        'background-color': '#f7f9fc',
                        'border': '2px solid #0056b3',
                        'border-radius': '5px',
                    }
                )
            ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'}),
            html.Div(
                id='hmw-data',
                children=[
                    html.H4("Peak Results", style={'text-align': 'center', 'color': '#0056b3'}),
                    dcc.Dropdown(
                        id='hmw-column-selector',
                        options=[
                            {"label": "Sample Name", "value": "Sample Name"},
                            {"label": "Main Peak Start", "value": "Main Peak Start"},
                            {"label": "Main Peak End", "value": "Main Peak End"},
                            {"label": "HMW Start", "value": "HMW Start"},
                            {"label": "HMW End", "value": "HMW End"},
                            {"label": "LMW Start", "value": "LMW Start"},
                            {"label": "LMW End", "value": "LMW End"},
                            {"label": "HMW Area", "value": "HMW Area"},
                            {"label": "Main Peak Area", "value": "Main Peak Area"},
                            {"label": "LMW Area", "value": "LMW Area"},
                            {"label": "HMW %", "value": "HMW"},
                            {"label": "Main Peak %", "value": "Main Peak"},
                            {"label": "LMW %", "value": "LMW"}
                        ],
                        value=["Sample Name", "HMW", "Main Peak", "LMW"],  # Default columns
                        multi=True,
                        placeholder="Select columns to display",
                        style={'margin-bottom': '10px'}
                    ),
                    dash_table.DataTable(
                        id='hmw-table',
                        columns=[  # Default columns for initialization
                            {"name": "Sample Name", "id": "Sample Name"},
                            {"name": "HMW %", "id": "HMW"},
                            {"name": "Main Peak %", "id": "Main Peak"},
                            {"name": "LMW %", "id": "LMW"}
                        ],
                        data=[],  # Dynamically updated by the callback
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'center', 'padding': '5px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                    ),
                    html.Button("Export to XLSX", id="export-button", style={
                        'margin-top': '10px',
                        'background-color': '#0056b3',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px',
                        'font-size': '14px',
                        'cursor': 'pointer',
                        'border-radius': '5px'
                    }),
                    dcc.Download(id="download-hmw-data")
                ],
                style={
                    'width': '68%',
                    'padding': '10px',
                    'border': '2px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#f7f9fc'
                }
            ),
            html.Div(
                id='sample-details',
                children=[
                    html.H4("Sample Details", style={'text-align': 'center', 'color': '#0056b3'}),
                    dash_table.DataTable(
                        id='sample-details-table',
                        columns=[
                            {"name": "Field", "id": "field"},
                            {"name": "Value", "id": "value"}
                        ],
                        data=[
                            {"field": "Sample Set Name", "value": ""},
                            {"field": "Column Name", "value": ""},
                            {"field": "Column Serial Number", "value": ""},
                            {"field": "Instrument Method Name", "value": ""},
                            {"field": "STD ID", "value": ""}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '5px',
                            'border': '1px solid #ddd',
                            'backgroundColor': '#f7f9fc',
                        },
                        style_header={
                            'backgroundColor': '#0056b3',
                            'fontWeight': 'bold',
                            'color': 'white',
                            'textAlign': 'center',
                        },
                    )
                ],
                style={
                    'width': '68%',
                    'margin-top': '20px',
                    'padding': '10px',
                    'border': '2px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#f7f9fc'
                }
            ),
            html.Div(
                id='standard-analysis',
                children=[
                    html.H4("Standard Analysis", style={'text-align': 'center', 'color': '#0056b3'}),
                    html.Div(
                        id='standard-analysis-content',
                        children=[
                            dcc.Graph(id='regression-plot', style={'margin-top': '20px'}),
                            dash_table.DataTable(
                                id="standard-table",
                                columns=[
                                    {"name": "Peak Name", "id": "peak_name"},
                                    {"name": "Retention Time", "id": "peak_retention_time"},
                                    {"name": "MW", "id": "MW"},
                                    {"name": "Asymmetry at 10%", "id": "asym_at_10"},
                                    {"name": "Plate Count", "id": "plate_count"},
                                    {"name": "Res-HH", "id": "res_hh"},
                                    {"name": "Performance Cutoff", "id": "performance_cutoff"},
                                    {"name": "Pass/Fail", "id": "pass/fail"},
                                ],
                                data=[],
                                row_selectable='multi',  # Allow multiple rows to be selected
                                selected_rows=[i for i in range(6)],  # Default: select all rows in `data`
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
                    html.P("Estimated MW for RT: ", id="estimated-mw"),
                    dcc.Input(
                        id="rt-input",
                        type="number",
                        placeholder="Enter Retention Time",
                        style={'width': '80%', 'margin-top': '10px'}
                    ),
                    html.Button("Calculate MW", id="calculate-mw-button", style={
                        'background-color': '#0056b3',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px',
                        'cursor': 'pointer',
                        'border-radius': '5px'
                    }),
                ],
                style={
                    'width': '68%',  # Match the width of the Sample Details box
                    'margin-top': '20px',
                    'padding': '10px',
                    'border': '2px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#f7f9fc'
                }
            ),
        ], style={'width': '80%', 'padding': '10px', 'overflow-y': 'auto'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'})
])




def get_std_result_id(sample_set_name=None, system_name=None):
    """
    Determine the standard result ID dynamically based on sample set and system name.

    Args:
        sample_set_name (str): The sample set name for filtering (optional).
        system_name (str): The system name for filtering (optional).

    Returns:
        Tuple: (std_result_id, std_sample) where std_result_id is the result ID or "No STD Found",
        and std_sample is the SampleMetadata object for the standard.
    """
    try:
        # Primary STD search: Check for an STD in the same sample set and system
        std_sample = SampleMetadata.objects.filter(
            sample_set_name=sample_set_name,
            sample_prefix="STD",
            system_name=system_name
        ).first()

        # Secondary STD search: Broad search if no specific match found
        if not std_sample:
            std_sample = SampleMetadata.objects.filter(sample_prefix="STD").first()

        std_result_id = std_sample.result_id if std_sample else "No STD Found"
        return std_result_id, std_sample

    except Exception as e:
        print(f"Error determining standard result ID: {e}")
        return "No STD Found", None


@app.callback(
    Output("std-result-id-store", "data"),
    [
        Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks')
    ],
    prevent_initial_call=True
)
def store_std_result_id(report_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        return None

    # Determine the triggering report
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_data = eval(triggered_id)

    if 'report_name' not in triggered_data:
        return None

    report_name = triggered_data['report_name']
    report = Report.objects.filter(report_name=report_name).first()

    if not report:
        return None

    # Fetch the first sample name from the report's selected samples
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
    if not sample_list:
        return None

    first_sample_name = sample_list[0]
    sample_metadata = SampleMetadata.objects.filter(sample_name=first_sample_name).first()

    if not sample_metadata:
        return None

    # Retrieve the `std_result_id` using the centralized logic
    std_result_id, _ = get_std_result_id(
        sample_set_name=sample_metadata.sample_set_name,
        system_name=sample_metadata.system_name
    )

    return std_result_id


@app.callback(
    Output({'type': 'contents', 'project_id': dash.dependencies.MATCH}, 'style'),
    Input({'type': 'folder', 'project_id': dash.dependencies.MATCH}, 'n_clicks'),
    State({'type': 'contents', 'project_id': dash.dependencies.MATCH}, 'style'),
    prevent_initial_call=True
)
def toggle_folder(n_clicks, current_style):
    """
    Toggle the visibility of folder contents when a project folder is clicked.
    """
    # Ensure we have a valid state before proceeding
    if current_style is None:
        current_style = {'display': 'none'}

    # Toggle the display state
    return {'display': 'block'} if current_style.get('display') == 'none' else {'display': 'none'}


# @app.callback(
#     Output("selected-report", "data"),
#     Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),
#     prevent_initial_call=True
# )
# def update_selected_report(report_clicks):
#     """
#     Update the selected report when a report is clicked.
#     """
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return dash.no_update
#
#     # Determine the triggered element
#     triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
#     try:
#         triggered_data = json.loads(triggered_id.replace("'", '"'))
#     except json.JSONDecodeError:
#         triggered_data = {}
#
#     # Ensure this was triggered by a report click
#     if triggered_data.get("type") != "report":
#         return dash.no_update
#
#     report_name = triggered_data.get("report_name", None)
#     print(f"Selected Report: {report_name}")
#     return report_name

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
        {"field": "Instrument Method Name", "value": ""},
        {"field": "STD ID", "value": ""}
    ]

    if not ctx.triggered:
        return default_data

    # Determine the triggering report
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_data = eval(triggered_id)

    if 'report_name' not in triggered_data:
        return default_data

    report_name = triggered_data['report_name']
    report = Report.objects.filter(report_name=report_name).first()

    if not report:
        return default_data

    # Fetch the first sample name from the report's selected samples
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
    if not sample_list:
        return default_data

    first_sample_name = sample_list[0]
    sample_metadata = SampleMetadata.objects.filter(sample_name=first_sample_name).first()

    if not sample_metadata:
        return default_data

    # Extract details from the `SampleMetadata` model
    sample_set_name = sample_metadata.sample_set_name or "N/A"
    column_name = sample_metadata.column_name or "N/A"
    column_serial_number = sample_metadata.column_serial_number or "N/A"
    system_name = sample_metadata.system_name or "N/A"
    instrument_method_name = sample_metadata.instrument_method_name or "N/A"

    # Primary STD search: Check for an STD in the same sample set
    std_sample = SampleMetadata.objects.filter(
        sample_set_name=sample_set_name, sample_prefix="STD"
    ).first()

    # Use centralized function to determine the STD ID
    std_result_id, _ = get_std_result_id(sample_set_name=sample_set_name, system_name=system_name)

    # Return table data
    return [
        {"field": "Sample Set Name", "value": sample_set_name},
        {"field": "Column Name", "value": column_name},
        {"field": "Column Serial Number", "value": column_serial_number},
        {"field": "Instrument Method Name", "value": instrument_method_name},
        {"field": "STD ID", "value": std_result_id}
    ]


import pandas as pd
import numpy as np


@app.callback(
    [
        Output("regression-equation", "children"),
        Output("r-squared-value", "children"),
        Output("regression-plot", "figure"),
        Output("estimated-mw", "children"),
        Output("standard-table", "data"),
        Output("regression-parameters", "data"),  # Store slope and intercept
    ],
    [
        Input("std-result-id-store", "data"),  # Use the stored std_result_id
        Input("standard-table", "selected_rows"),  # Selected rows for regression
        State("standard-table", "data"),
        State("rt-input", "value"),
    ],
    prevent_initial_call=True
)
def standard_analysis(std_result_id, selected_rows, table_data, rt_input):
    # print(std_result_id)
    if not std_result_id or std_result_id == "No STD Found":
        return "No STD Selected", "N/A", {}, "N/A", [], {'slope': 0, 'intercept': 0}

    # Query peak results
    peak_results = PeakResults.objects.filter(result_id=std_result_id).values(
        "peak_name", "peak_retention_time", "asym_at_10", "plate_count", "res_hh"
    )
    df = pd.DataFrame(list(peak_results))
    if df.empty:
        return "No Peak Results Found", "N/A", {}, "N/A", [], {'slope': 0, 'intercept': 0}
    # Define the ordered peak names
    ordered_peak_names = [
        "Peak1-Thyroglobulin",
        "Peak2-Thyroglobulin",
        "Peak3-IgG",
        "Peak4-BSA",
        "Peak5-Myoglobin",
        "Peak6-Uracil"
    ]

    # Sort the DataFrame by retention time
    df = df.sort_values(by="peak_retention_time", ascending=True).reset_index(drop=True)

    # Drop any rows beyond the first 6
    if len(df) > 6:
        df = df.iloc[:6]

    # Assign peak names to the DataFrame
    df["peak_name"] = ordered_peak_names[:len(df)]  # Ensure names match the number of rows
    df["MW"] = df["peak_name"].map(MW_MAPPING)

    # Handle missing MW values
    df["MW"] = df["MW"].fillna("N/A")  # Replace with a default value if necessary
    df["MW"] = df["peak_name"].map(MW_MAPPING)
    # print(df)

    if df.empty:
        return "No Peak Results Found", "N/A", {}, "N/A", []

    # Molecular weight mapping
    PERFORMANCE_MAPPING = {
        'Peak1-Thyroglobulin': 1000,
        'Peak2-Thyroglobulin': 1000,
        'Peak3-IgG': 1000,
        'Peak4-BSA': 1000,
        'Peak5-Myoglobin': 1000,
        'Peak6-Uracil': 1000
    }

    # Add Performance column
    df["performance_cutoff"] = df["peak_name"].map(PERFORMANCE_MAPPING)

    # Add Pass/Fail column based on plate count
    def determine_pass_fail(row):
        # Ensure column_performance_cutoff is an integer
        column_performance_cutoff = PERFORMANCE_MAPPING.get(row["peak_name"], None)
        try:
            column_performance_cutoff = int(column_performance_cutoff)
        except (TypeError, ValueError):
            return "Fail"  # Default to "Fail" if the cutoff is invalid

        # Ensure plate_count is an integer
        try:
            plate_count = int(row["plate_count"])
        except (TypeError, ValueError):
            return "Fail"  # Default to "Fail" if plate_count is invalid

        # Compare plate_count to the cutoff
        if plate_count >= column_performance_cutoff:
            return "Pass"
        return "Fail"

    df["pass/fail"] = df.apply(determine_pass_fail, axis=1)
    # print(df)
    # Prepare table data
    table_data = df.to_dict("records")
    # print("Table Data for Display:", table_data)

    # Validate selected_rows
    if not selected_rows or not table_data:
        print("No rows selected or table data is empty.")
        return "No Points Selected for Regression", "N/A", {}, "N/A", table_data, {'slope': 0, 'intercept': 0}

    # Safely retrieve selected rows
    try:
        selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
    except IndexError as e:
        print(f"IndexError: {e}")
        selected_data = []

    if not selected_data:
        print("No valid data for selected rows.")
        return "No Points Selected for Regression", "N/A", {}, "N/A", table_data, {'slope': 0, 'intercept': 0}

    # Perform regression
    regression_df = pd.DataFrame(selected_data).dropna(subset=["MW", "peak_retention_time"])
    if regression_df.empty:
        return "Regression Data is Empty", "N/A", {}, "N/A", table_data, {'slope': 0, 'intercept': 0}

    try:
        slope, intercept, r_value, _, _ = linregress(
            regression_df["peak_retention_time"], np.log(regression_df["MW"])
        )
    except Exception as e:
        print(f"Regression error: {e}")
        return "Regression Failed", "N/A", {}, "N/A", table_data, {'slope': 0, 'intercept': 0}

    # Regression plot
    x_vals = np.linspace(
        regression_df["peak_retention_time"].min(),
        regression_df["peak_retention_time"].max(),
        100,
    )
    y_vals = slope * x_vals + intercept
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=regression_df["peak_retention_time"],
        y=np.log(regression_df["MW"]),
        mode="markers+text",
        text=regression_df["peak_name"],
        textposition="top center",
        name="Data Points"
    ))
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines", name="Regression Line"))
    fig.update_layout(
        title="Retention Time vs Log(MW)",
        xaxis_title="Retention Time",
        yaxis_title="Log(MW)",
        template="plotly_white"
    )

    # Estimate MW
    estimated_mw = "N/A"
    if rt_input is not None:
        log_mw = slope * rt_input + intercept
        estimated_mw = f"{np.exp(log_mw) / 1000:.2f} kD"

    return (
        f"y = {slope:.4f}x + {intercept:.4f}",
        f"R² = {r_value ** 2:.4f}",
        fig,
        estimated_mw,
        table_data,
        {'slope': slope, 'intercept': intercept}
    )


def generate_subplots_with_shading(sample_list, channels, enable_shading, enable_peak_labeling, main_peak_rt, slope,
                                   intercept, hmw_table_data):
    num_samples = len(sample_list)
    cols = 3
    rows = (num_samples // cols) + (num_samples % cols > 0)

    region_colors = {
        "HMW": "red",
        "MP": "blue",
        "LMW": "green"
    }

    label_offsets = {
        "HMW": {"x_offset": 0, "y_offset": 0.02},
        "MP": {"x_offset": 0, "y_offset": 0.02},
        "LMW": {"x_offset": 0, "y_offset": 0.02}
    }

    fig = make_subplots(
        rows=rows,
        cols=cols,
        start_cell="top-left",
        subplot_titles=sample_list,
        vertical_spacing=0.03,
        horizontal_spacing=0.05
    )

    for i, sample_name in enumerate(sample_list):
        row = (i // cols) + 1
        col = (i % cols) + 1
        sample = SampleMetadata.objects.filter(sample_name=sample_name).first()
        if not sample:
            continue
        time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
        df = pd.DataFrame(list(time_series.values()))

        # Get HMW Table row for the current sample
        hmw_row = next((row for row in hmw_table_data if row['Sample Name'] == sample_name), None)
        if not hmw_row:
            continue

        # Extract values from HMW Table
        main_peak_start = hmw_row.get("Main Peak Start", None)
        main_peak_end = hmw_row.get("Main Peak End", None)
        hmw_start = hmw_row.get("HMW Start", None)
        hmw_end = hmw_row.get("HMW End", None)
        lmw_start = hmw_row.get("LMW Start", None)
        lmw_end = hmw_row.get("LMW End", None)

        percentages = {
            "HMW": hmw_row.get("HMW", 0),
            "MP": hmw_row.get("Main Peak", 0),
            "LMW": hmw_row.get("LMW", 0)
        }

        for channel in channels:
            if channel in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        line=dict(color="blue"),
                        name=f"{sample_name} - {channel}"
                    ),
                    row=row,
                    col=col
                )

                if enable_shading:
                    # Define shading regions using HMW Table data
                    shading_regions = {
                        "HMW": (hmw_start, hmw_end),
                        "MP": (main_peak_start, main_peak_end),
                        "LMW": (lmw_start, lmw_end)
                    }

                    for region, (start_time, end_time) in shading_regions.items():
                        try:
                            # Ensure numeric comparison
                            start_time = float(start_time) if pd.notna(start_time) else None
                            end_time = float(end_time) if pd.notna(end_time) else None
                        except ValueError:
                            start_time = end_time = None

                        if start_time is None or end_time is None:
                            continue  # Skip invalid regions

                        shading_region = df[(df['time'] >= start_time) & (df['time'] <= end_time)]
                        if not shading_region.empty:
                            fig.add_trace(
                                go.Scatter(
                                    x=shading_region['time'],
                                    y=shading_region[channel],
                                    fill='tozeroy',
                                    mode='none',
                                    fillcolor=region_colors[region],
                                    opacity=0.05,
                                    name=f"{region} ({sample_name})"
                                ),
                                row=row,
                                col=col
                            )

                            if enable_peak_labeling:
                                # Annotate peaks using max value in the region
                                try:
                                    max_peak_row = shading_region.loc[shading_region[channel].idxmax()]
                                    max_retention_time = max_peak_row['time']
                                    max_peak_value = max_peak_row[channel]

                                    # Calculate MW using the max retention time
                                    log_mw = slope * max_retention_time + intercept
                                    mw = round(np.exp(log_mw) / 1000, 2)

                                    # Debug MW calculation
                                    # print(f"Sample: {sample_name}, Region: {region}, Max Retention Time: {max_retention_time}, MW: {mw}")

                                    # Apply offsets for labels
                                    x_offset = label_offsets[region]["x_offset"] + max_retention_time
                                    y_offset = label_offsets[region]["y_offset"] + max_peak_value

                                    fig.add_annotation(
                                        x=x_offset,
                                        y=y_offset,
                                        text=f"{region}:{percentages[region]}%<br>MW:{mw} kD",
                                        showarrow=False,
                                        font=dict(size=12, color="black"),
                                        align="center",
                                        bgcolor="rgba(255, 255, 255, 0.8)",
                                        bordercolor="black",
                                        row=row,
                                        col=col
                                    )
                                except Exception as e:
                                    print(f"Error annotating MW for {sample_name}, {region}: {e}")

        fig.update_xaxes(
            title_text="Time (min)",
            title_standoff=3,
            row=row,
            col=col
        )
        fig.update_yaxes(
            title_text="UV280",
            title_standoff=3,
            row=row,
            col=col
        )
    fig.update_layout(
        height=350 * rows,
        margin=dict(l=10, r=10, t=50, b=10),
        title_x=0.5,
        showlegend=False,
        plot_bgcolor="white"
    )

    return fig


@app.callback(
    [
        Output('time-series-graph', 'figure'),
        Output('time-series-graph', 'style'),
        Output('selected-report', 'data')
    ],
    [
        Input('plot-type-dropdown', 'value'),  # Trigger on plot type change
        Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),  # Trigger on report change
        Input('shading-checklist', 'value'),  # Trigger on shading enable/disable
        Input('peak-label-checklist', 'value'),  # Trigger on peak labeling enable/disable
        Input('main-peak-rt-input', 'value'),  # Trigger on Main Peak RT change
        Input('low-mw-cutoff-input', 'value'),  # Trigger on LMW Cutoff change
        Input('regression-parameters', 'data'),  # Regression parameters for peak labeling
        Input('hmw-table-store', 'data'),  # HMW data changes
        Input('channel-checklist', 'value'),  # Trigger on channel selection
    ],
    [
        State('selected-report', 'data')  # Persist the current selected report
    ],
    prevent_initial_call=True
)
def update_graph(plot_type, report_clicks, shading_options, peak_label_options,
                 main_peak_rt, low_mw_cutoff, regression_params, hmw_table_data,
                 selected_channels, selected_report):
    ctx = dash.callback_context

    # Determine which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_data = json.loads(triggered_id.replace("'", '"'))
    except json.JSONDecodeError:
        triggered_data = {}

    # Get the report name
    report_name = triggered_data.get('report_name', selected_report)

    # If no report is selected or provided, return empty figure
    if not report_name:
        return go.Figure().update_layout(title="No Report Selected"), {'display': 'block'}, selected_report

    # Fetch the selected report
    report = Report.objects.filter(report_name=report_name).first()
    if not report:
        return go.Figure(), {'display': 'block'}, selected_report

    # Retrieve the list of selected samples
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]

    if plot_type == 'plotly':
        # Generate the Plotly graph
        fig = go.Figure()
        for sample_name in sample_list:
            sample = SampleMetadata.objects.filter(sample_name=sample_name).first()
            if not sample:
                continue
            time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
            df = pd.DataFrame(list(time_series.values()))
            for channel in selected_channels:
                if channel in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        name=f"{sample.sample_name} - {channel}"
                    ))

        # Update layout for Plotly graph
        fig.update_layout(
            title='Time Series Data',
            xaxis_title='Time (Minutes)',
            yaxis_title='UV280',
            template='plotly_white',
            height=800
        )
        return fig, {'display': 'block'}, report_name  # Show Plotly graph and persist report

    elif plot_type == 'subplots':
        if not hmw_table_data:
            return go.Figure(), {'display': 'block'}, report_name

        # Extract slope and intercept from regression parameters
        slope = regression_params.get('slope', 0)
        intercept = regression_params.get('intercept', 0)
        enable_shading = 'enable_shading' in shading_options
        enable_peak_labeling = 'enable_peak_labeling' in peak_label_options

        # Generate subplots with dynamic shading and peak labeling
        fig = generate_subplots_with_shading(
            sample_list,
            selected_channels,
            enable_shading=enable_shading,
            enable_peak_labeling=enable_peak_labeling,
            main_peak_rt=main_peak_rt,
            slope=slope,
            intercept=intercept,
            hmw_table_data=hmw_table_data
        )

        return fig, {'display': 'block'}, report_name

    return go.Figure(), {'display': 'block'}, report_name


@app.callback(
    Output("download-hmw-data", "data"),
    Input("export-button", "n_clicks"),
    State("hmw-table", "data"),
    prevent_initial_call=True
)
def export_to_xlsx(n_clicks, table_data):
    if not table_data:
        return dash.no_update  # Do nothing if the table is empty

    # Convert table data to a pandas DataFrame
    df = pd.DataFrame(table_data)

    # Use Dash's `send_data_frame` to export the DataFrame as an XLSX file
    return dcc.send_data_frame(df.to_excel, "HMW_Table.xlsx", index=False)


@app.callback(
    [Output('main-peak-rt-store', 'data'), Output('low-mw-cutoff-store', 'data')],
    [Input('main-peak-rt-input', 'value'), Input('low-mw-cutoff-input', 'value')],
    prevent_initial_call=True
)
def update_cutoff_values(main_peak_rt, low_mw_cutoff):
    print(f"Updated Main Peak RT: {main_peak_rt}, LMW Cutoff: {low_mw_cutoff}")
    return main_peak_rt, low_mw_cutoff


@app.callback(
    [Output('hmw-table', 'columns'), Output('hmw-table', 'data'), Output('hmw-table-store', 'data')],
    [
        Input('hmw-column-selector', 'value'),  # User-selected columns
        Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),  # Trigger on report change
        Input('main-peak-rt-input', 'value'),  # Main Peak RT
        Input('low-mw-cutoff-input', 'value')  # LMW Cutoff
    ],
    [State('selected-report', 'data')],  # Use the stored selected report
    prevent_initial_call=True
)
def update_hmw_table(selected_columns, report_clicks, main_peak_rt, low_mw_cutoff, selected_report):
    ctx = dash.callback_context

    # Debugging triggered input
    print(f"Triggered ID: {ctx.triggered[0]['prop_id']}")
    print(f"Main Peak RT: {main_peak_rt}, LMW Cutoff: {low_mw_cutoff}")
    print(f"Selected Report: {selected_report}")

    # Ensure valid numeric inputs
    if main_peak_rt is None or low_mw_cutoff is None:
        print("Invalid Main Peak RT or LMW Cutoff values.")
        return [], [], []

    # Use the stored selected report
    if not selected_report:
        print("No report found or selected.")
        return [], [], []

    report = Report.objects.filter(report_name=selected_report).first()
    if not report:
        print(f"Report '{selected_report}' not found in the database.")
        return [], [], []

    # Generate HMW Table
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
    if not sample_list:
        print("No samples found in the selected report.")
        return [], [], []

    summary_data = []

    for sample_name in sample_list:
        sample = SampleMetadata.objects.filter(sample_name=sample_name).first()
        if not sample:
            continue

        peak_results = PeakResults.objects.filter(result_id=sample.result_id)
        if not peak_results.exists():
            continue

        df = pd.DataFrame.from_records(peak_results.values())
        print(df)
        if 'peak_retention_time' in df.columns:
            df['peak_retention_time'] = pd.to_numeric(df['peak_retention_time'], errors='coerce')
            df = df.dropna(subset=['peak_retention_time'])  # Drop invalid rows
            df['area'] = df['area'].astype(float)
            df['peak_start_time'] = df['peak_start_time'].astype(float)
            df['peak_end_time'] = df['peak_end_time'].astype(float)

            try:
                closest_index = (df['peak_retention_time'] - main_peak_rt).abs().idxmin()
            except ValueError:
                print("Error finding closest index for Main Peak RT.")
                continue

            main_peak_area = round(df.loc[closest_index, 'area'], 2)
            main_peak_start = df.loc[closest_index, 'peak_start_time']
            main_peak_end = df.loc[closest_index, 'peak_end_time']

            hmw_start = df[df['peak_retention_time'] < main_peak_start]['peak_start_time'].min()
            hmw_end = main_peak_start

            lmw_start = main_peak_end
            lmw_end = df[df['peak_retention_time'] > main_peak_end]['peak_end_time'].max()

            df_excluding_main_peak = df.drop(index=closest_index)

            hmw_area = round(
                df_excluding_main_peak[df_excluding_main_peak['peak_retention_time'] < main_peak_rt]['area'].sum(),
                2
            )

            lmw_area = round(
                df_excluding_main_peak[
                    (df_excluding_main_peak['peak_retention_time'] > main_peak_rt) &
                    (df_excluding_main_peak['peak_retention_time'] <= low_mw_cutoff)
                    ]['area'].sum(),
                2
            )

            total_area = main_peak_area + hmw_area + lmw_area
            hmw_percent = round((hmw_area / total_area) * 100, 2) if total_area > 0 else 0
            main_peak_percent = round((main_peak_area / total_area) * 100, 2) if total_area > 0 else 0
            lmw_percent = round((lmw_area / total_area) * 100, 2) if total_area > 0 else 0

            summary_data.append({
                'Sample Name': sample.sample_name,
                'Main Peak Start': main_peak_start if pd.notna(main_peak_start) else "N/A",
                'Main Peak End': main_peak_end if pd.notna(main_peak_end) else "N/A",
                'HMW Start': hmw_start if pd.notna(hmw_start) else "N/A",
                'HMW End': hmw_end if pd.notna(hmw_end) else "N/A",
                'LMW Start': lmw_start if pd.notna(lmw_start) else "N/A",
                'LMW End': lmw_end if pd.notna(lmw_end) else "N/A",
                'HMW': hmw_percent,
                'Main Peak': main_peak_percent,
                'LMW': lmw_percent
            })

    # Debug the generated summary data
    print(f"Summary Data: {summary_data}")

    # Define the desired column order
    desired_order = [
        'Sample Name', 'HMW', 'HMW Start', 'HMW End',
        'Main Peak', 'Main Peak Start', 'Main Peak End',
        'LMW', 'LMW Start', 'LMW End'
    ]

    selected_columns = selected_columns if selected_columns else []
    all_columns = list(set(['Sample Name', 'HMW', 'Main Peak', 'LMW'] + selected_columns))
    ordered_columns = [col for col in desired_order if col in all_columns]

    # Create table columns dynamically
    table_columns = [{"name": col, "id": col} for col in ordered_columns]
    filtered_data = [{col: row[col] for col in ordered_columns if col in row} for row in summary_data]

    return table_columns, filtered_data, summary_data


@app.callback(
    Output("selected-report-display", "children"),
    Input("selected-report", "data")
)
def display_selected_report(selected_report):
    if not selected_report:
        return "No report selected"
    return f"Currently Selected Report: {selected_report}"
