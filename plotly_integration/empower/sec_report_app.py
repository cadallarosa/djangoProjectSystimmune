import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django_plotly_dash import DjangoDash
import dash
from dash import dcc, html, Input, Output, State, dash_table, Dash, MATCH, callback_context
import pandas as pd
from scipy.stats import linregress
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
app = DjangoDash('SecReportApp')


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
    # ✅ Filter only reports with analysis_type = 1 (SEC)
    filtered_reports = Report.objects.filter(analysis_type=1).values(
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
    dcc.Store(id='regression-parameters', data={'slope': 0, 'intercept': 0}),
    dcc.Store(id='main-peak-rt-store', data=None),  # Default value for main peak RT
    dcc.Store(id='low-mw-cutoff-store', data=12),  # Default value for low MW cutoff
    dcc.Store(id='hmw-table-store', data=[]),
    dcc.Store(id='report-list-store', data=[]),

    # Top-left Home Button
    # html.Div(
    #     html.Button("Home", id="home-btn", style={
    #         'background-color': '#0056b3',
    #         'color': 'white',
    #         'border': 'none',
    #         'padding': '10px 20px',
    #         'font-size': '16px',
    #         'cursor': 'pointer',
    #         'border-radius': '5px'
    #     }),
    #     style={'margin': '10px'}
    # ),
    html.Div([  # Main layout with sidebar and content areas
        html.Div(  # Sidebar
            id='sidebar',
            children=generate_sidebar(initial_projects),
            style={
                'width': '20%',
                'height': '100%)',
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
                    html.Div([  # Plot and settings
                        dcc.Store(id='selected-report', data={}),  # Add this line for state persistence
                        html.Div(  # Plot area
                            id='plot-area',
                            children=[
                                html.H4("SEC Results", id="sec-results-header",
                                        style={'text-align': 'center', 'color': '#0056b3'}),
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
                                            height=800,  # Adjust height (default is 400)
                                            dragmode="select",
                                            annotations=[
                                                {
                                                    # "showarrow": True
                                                }
                                            ]
                                        )
                                    ),
                                    config={  # ✅ Correct placement
                                        'toImageButtonOptions': {
                                            'filename': 'custom_name'},
                                        'edits': {"annotationPosition": True}}

                                )
                            ],
                            style={
                                'width': '85%',
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
                                        {'label': 'UV280', 'value': 'channel_1'},
                                        {'label': 'UV260', 'value': 'channel_2'},
                                        {'label': 'Pressure', 'value': 'channel_3'}
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
                                        value=7.843,  # Default
                                        style={'width': '100%'}
                                    ),
                                    dcc.Store(id='main-peak-rt-store', data=5.10),
                                ], style={'margin-top': '10px'}),

                                html.Button("Refresh RT", id="refresh-rt-btn", n_clicks=0, style={
                                    'background-color': '#0056b3',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '10px',
                                    'font-size': '14px',
                                    'cursor': 'pointer',
                                    'border-radius': '5px',
                                    'margin-left': '0px',
                                    'margin-top': '15px',  # Adds space above the button
                                    'margin-bottom': '15px'  # Adds space below the button
                                }),

                                html.Div([
                                    html.Label("LMW Cutoff Time:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='low-mw-cutoff-input',
                                        type='number',
                                        value=12,  # Default value
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
                                ),
                                html.Div([
                                    html.Label("Number of Columns:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='num-cols-input',
                                        type='number',
                                        min=1,
                                        step=1,
                                        value=3,  # Default value
                                        debounce=True,
                                        style={'width': '100%'}
                                    )
                                ], style={'margin-top': '10px'}),

                                html.Div([
                                    html.Label("Vertical Spacing:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='vertical-spacing-input',
                                        type='number',
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        value=0.05,  # Default value
                                        style={'width': '100%'}
                                    )
                                ], style={'margin-top': '10px'}),
                                html.Div([
                                    html.Label("Horizontal Spacing:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='horizontal-spacing-input',
                                        type='number',
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        value=0.05,  # Default value
                                        style={'width': '100%'}
                                    )
                                ], style={'margin-top': '10px'}),

                            ],
                            style={
                                'height': '100%',
                                'width': '15%',
                                'padding': '10px',
                                'background-color': '#f7f9fc',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                            }

                        )
                    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'}),
                ]),

                # 🔹 Tab 2: Standard Analysis
                dcc.Tab(label="Table Data", value="tab-2", children=[
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
                                sort_action="native",
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
                            'width': '98%',
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
                            'width': '98%',
                            'margin-top': '20px',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc'
                        }
                    ),
                ]),

                # 🔹 Tab 2: Standard Analysis
                dcc.Tab(label="Standard Analysis", value="tab-3", children=[
                    html.Div(
                        id='standard-analysis',
                        children=[
                            html.H4("Standard Analysis", style={'text-align': 'center', 'color': '#0056b3'}),

                            # 🔹 Standard ID Dropdown
                            html.Div([
                                html.Label("Select Standard ID:", style={'color': '#0056b3'}),
                                dcc.Dropdown(
                                    id='standard-id-dropdown',
                                    placeholder="Select a Standard ID",
                                    value='',
                                    style={'width': '100%'}
                                )
                            ], style={'margin-top': '10px'}),

                            html.Div(
                                id='standard-analysis-content',
                                children=[
                                    # 🔹 Standard Peak Plot
                                    dcc.Graph(
                                        id='standard-peak-plot',
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
                                                height=375,  # Adjust height (default is 400)
                                                dragmode="select",
                                            )
                                        ),

                                        style={'margin-top': '10px'}
                                    )],
                                style={
                                    'padding': '10px',
                                    'border': '2px solid #0056b3',
                                    'border-radius': '5px',
                                    'background-color': '#f7f9fc',
                                    'margin-top': '20px',
                                }
                            ),

                            html.Div(
                                id='standard-analysis-content',
                                children=[
                                    dcc.Graph(
                                        id='regression-plot',
                                        figure=go.Figure(
                                            data=[go.Scatter(
                                                x=[],
                                                y=[],
                                                mode='lines',
                                                line=dict(dash='dash'),  # ✅ Makes the line dashed
                                            )],
                                            layout=go.Layout(
                                                title="Sample Plot",
                                                xaxis_title="Retention Time (min)",
                                                yaxis_title="Log(MW)",
                                                height=375,  # Adjust height (default is 400)
                                                dragmode="select",
                                            )
                                        ),
                                        style={'margin-top': '20px'}),
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
                                        selected_rows=[i for i in range(4)],  # Default: select all rows in `data`
                                        style_table={'overflowX': 'auto'},
                                        style_cell={'textAlign': 'center', 'padding': '5px'},
                                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                                    )
                                ],
                                style={
                                    'padding': '10px',
                                    'margin-top': '20px',
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
                            'width': '98%',  # Match the width of the Sample Details box
                            'margin-top': '20px',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc'
                        }
                    )
                ])
            ])
        ], style={'width': '80%', 'padding': '10px', 'overflow-y': 'auto'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'})
])


@app.callback(
    Output("sec-results-header", "children"),  # Update the SEC Results header
    [Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def update_sec_results_header(report_clicks):
    ctx = dash.callback_context  # Correctly access callback context

    if not ctx.triggered:
        return "SEC Results"

    # Extract triggered report name
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        triggered_data = eval(triggered_id)  # Convert string ID to dictionary
    except Exception:
        return "Error: Invalid Report Data"

    if 'report_name' not in triggered_data:
        return "SEC Results"

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
        {"field": "Instrument Method Name", "value": instrument_method_name},

    ]


def get_filtered_std_ids(report_id):
    """
    Retrieve all standard result IDs from the most relevant sample set for the given report ID,
    including the associated sample names.

    Args:
        report_id (str): The ID of the selected report.

    Returns:
        List[Tuple]: A list of tuples containing (std_result_id, sample_name, std_sample).
    """
    try:
        # Retrieve the report
        report = Report.objects.filter(report_id=report_id).first()
        if not report:
            return [("No STD Found", "Unknown Sample", None)]  # Ensure return format is consistent

        # Extract selected sample names **with exact match**
        selected_result_ids = [result_id.strip() for result_id in report.selected_result_ids.split(",") if
                               result_id.strip()]

        # Fetch all sample set names **linked to the exact selected samples**
        sample_set_entries = SampleMetadata.objects.filter(result_id__in=selected_result_ids) \
            .values_list("sample_name", "sample_set_name")

        # Count occurrences of each sample set
        sample_set_counts = Counter([entry[1] for entry in sample_set_entries])

        # If no sample sets are found, return an empty result
        if not sample_set_counts:
            return [("No STD Found", "Unknown Sample", None)]

        # Select the most common sample set (assumes correct set has most samples)
        most_common_sample_set = sample_set_counts.most_common(1)[0][0]

        # Debugging Output
        print(f"Extracted Sample Names: {selected_result_ids}")
        print(f"Detected Sample Set Names: {list(sample_set_counts.keys())}")
        print(f"✔ Using Most Common Sample Set: {most_common_sample_set}")

        # Retrieve standard IDs **only from this sample set**
        std_samples = SampleMetadata.objects.filter(
            sample_set_name=most_common_sample_set,  # Ensure correct filtering
            sample_prefix="STD"
        ).distinct()

        std_result_list = []
        for sample in std_samples:
            std_id = sample.result_id
            sample_name = getattr(sample, "sample_name", "Unknown Sample")  # Handle missing sample name safely
            std_result_list.append((std_id, sample_name, sample))

        return std_result_list if std_result_list else [("No STD Found", "Unknown Sample", None)]

    except Exception as e:
        print(f"Error retrieving standard result IDs: {e}")
        return [("No STD Found", "Unknown Sample", None)]


@app.callback(
    [
        Output('standard-id-dropdown', 'options'),  # Update dropdown options
        Output("std-result-id-store", "data"),  # Store first available standard ID
        Output('standard-id-dropdown', 'value')
    ],
    [Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def update_standard_id_dropdown(report_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        return [], None  # Return empty dropdown and reset storage

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        triggered_data = eval(triggered_id)  # Convert string ID to dictionary
    except Exception:
        return [], None

    if 'report_name' not in triggered_data:
        return [], None

    report_name = triggered_data['report_name']
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        return [], None

    # Retrieve standard IDs using the updated function
    std_results = get_filtered_std_ids(report.report_id)

    # Format dropdown options with sample name and standard ID
    dropdown_options = [
        {'label': f"{sample_name} - STD {std_id}", 'value': std_id}
        for std_id, sample_name, _ in std_results if std_id != "No STD Found"
    ]

    # Automatically select the first standard ID
    first_std_id = dropdown_options[0]['value'] if dropdown_options else "No STD Found"

    print(f"🔄 Auto-selecting first standard: {first_std_id}")  # Debugging

    return dropdown_options, first_std_id, first_std_id


def get_top_peaks(result_id):
    """
    Fetch and process the top 6 peaks by area for a given standard result ID.
    Returns a DataFrame with ordered peak names.
    """
    # Fetch peak results
    peaks = PeakResults.objects.filter(result_id=result_id).values(
        "peak_name", "peak_retention_time", "height", "area", "asym_at_10", "plate_count", "res_hh"
    )
    df = pd.DataFrame(list(peaks))

    if df.empty:
        return df  # Return empty DataFrame if no peaks found
    time_cutoff = 18
    df = df[df["peak_retention_time"] <= time_cutoff]
    # Define the ordered peak names
    ordered_peak_names = [
        "Peak1-Thyroglobulin",
        "Peak2-IgG",
        "Peak3-BSA",
        "Peak4-Myoglobin",
        "Peak5-Uracil"
    ]

    # Step 1: Sort peaks by area (descending) and keep only the top 6 peaks
    df = df.sort_values(by="area", ascending=False).reset_index(drop=True)
    df = df.iloc[:5] if len(df) > 5 else df  # Keep only the top 6 peaks

    # Step 2: Reorder the selected peaks by retention time (ascending)
    df = df.sort_values(by="peak_retention_time", ascending=True).reset_index(drop=True)

    # Step 3: Assign peak names from ordered list
    df["peak_name"] = ordered_peak_names[:len(df)]

    return df


@app.callback(
    Output('standard-peak-plot', 'figure'),
    Input('standard-id-dropdown', 'value'),
    prevent_initial_call=True
)
def update_standard_plot(standard_id):
    if not standard_id or standard_id == "No STD Found":
        return go.Figure()

    # Fetch time series data
    time_series = TimeSeriesData.objects.filter(result_id=standard_id).values("time", "channel_1")
    df_time = pd.DataFrame(time_series)

    if df_time.empty:
        return go.Figure()

    # Fetch and process the top 6 peaks
    df_peaks = get_top_peaks(standard_id)

    if df_peaks.empty:
        return go.Figure()

    # Function to find the closest y-value in time series for a given retention time
    def get_closest_time_series_value(retention_time):
        closest_idx = (df_time["time"] - retention_time).abs().idxmin()
        return df_time.loc[closest_idx, "channel_1"] if closest_idx in df_time.index else None

    # Create Plotly figure
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=df_time["time"], y=df_time["channel_1"], mode='lines', name=f"STD {standard_id} - Channel 1"))

    # Ensure annotation is placed at the correct peak height from time series
    for _, row in df_peaks.iterrows():
        y_value = get_closest_time_series_value(row["peak_retention_time"])
        if y_value is not None:
            fig.add_annotation(x=row["peak_retention_time"], y=y_value, text=row["peak_name"], showarrow=True,
                               arrowhead=2)

    fig.update_layout(title=f"Time Series for Standard ID {standard_id}", xaxis_title="Time (min)",
                      yaxis_title="UV280", template="plotly_white")
    return fig


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
        Input('standard-id-dropdown', 'value'),
        Input("standard-table", "selected_rows"),  # Ensure selection is passed
        State("standard-table", "data"),
        State("rt-input", "value"),
    ],
    prevent_initial_call=True
)
def standard_analysis(std_result_id, selected_rows, table_data, rt_input):
    if not std_result_id or std_result_id == "No STD Found":
        return "No STD Selected", "N/A", {}, "N/A", [], {'slope': 0, 'intercept': 0}

    # Fetch and process the top 6 peaks
    df = get_top_peaks(std_result_id)

    if df.empty:
        return "No Peak Results Found", "N/A", {}, "N/A", [], [], {'slope': 0, 'intercept': 0}

    # Assign Molecular Weight (MW)
    MW_MAPPING = {
        'Peak1-Thyroglobulin': 660000,
        'Peak2-IgG': 150000,
        'Peak3-BSA': 66400,
        'Peak4-Myoglobin': 17000,
        'Peak5-Uracil': 112
    }
    # Molecular weight mapping
    PERFORMANCE_MAPPING = {
        'Peak1-Thyroglobulin': 1000,
        'Peak2-IgG': 1000,
        'Peak3-BSA': 1000,
        'Peak4-Myoglobin': 1000,
        'Peak5-Uracil': 1000
    }
    df["MW"] = df["peak_name"].map(MW_MAPPING).fillna("N/A")

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

    # Prepare table data
    table_data = df.to_dict("records")

    # **Ensure user selection persists**
    if not selected_rows or not table_data:
        return "No Points Selected for Regression", "N/A", {}, "N/A", table_data, selected_rows, {'slope': 0,
                                                                                                  'intercept': 0}

    # Retrieve selected peaks
    selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
    regression_df = pd.DataFrame(selected_data).dropna(subset=["MW", "peak_retention_time"])

    if regression_df.empty:
        return "Regression Data is Empty", "N/A", {}, "N/A", table_data, selected_rows, {'slope': 0, 'intercept': 0}

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

    # **Generate regression plot**
    x_vals = np.linspace(regression_df["peak_retention_time"].min(), regression_df["peak_retention_time"].max(), 100)
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
    fig.add_trace(go.Scatter
                  (x=x_vals,
                   y=y_vals,
                   mode="lines",
                   name="Regression Line",
                   line=dict(dash='dash')  # ✅ Makes the regression line dashed
                   ))
    fig.update_layout(
        title="Retention Time vs Log(MW)",
        xaxis_title="Retention Time (min)",
        yaxis_title="Log(MW)",
        template="plotly_white"
    )

    # **Estimate MW**
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


def generate_subplots_with_shading(selected_result_ids, sample_list, channels, enable_shading, enable_peak_labeling,
                                   main_peak_rt, slope,
                                   intercept, hmw_table_data, num_cols=3, vertical_spacing=0.05,
                                   horizontal_spacing=0.5):
    num_samples = len(sample_list)
    cols = num_cols
    rows = (num_samples // cols) + (num_samples % cols > 0)

    region_colors = {
        "HMW": "rgba(255, 87, 87, 0.85)",  # Coral Red
        "MP": "rgba(72, 149, 239, 0.85)",  # Sky Blue
        "LMW": "rgba(122, 230, 160, 0.85)"  # Mint Green
    }

    label_offsets = {
        "HMW": {"x_offset": -3, "y_offset": 0.02},
        "MP": {"x_offset": 0, "y_offset": 0.02},
        "LMW": {"x_offset": 2, "y_offset": 0.02}
    }

    fig = make_subplots(
        rows=rows,
        cols=cols,
        start_cell="top-left",
        subplot_titles=sample_list,  # NEED TO FIX THIS
        vertical_spacing=vertical_spacing,
        horizontal_spacing=horizontal_spacing
    )

    for i, result_id in enumerate(selected_result_ids):
        row = (i // cols) + 1
        col = (i % cols) + 1
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            continue
        time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
        df = pd.DataFrame(list(time_series.values()))
        sample_name = sample.sample_name
        # Get HMW Table row for the current sample
        # ✅ Find HMW row safely
        hmw_row = next((r for r in hmw_table_data if isinstance(r, dict) and r.get('Sample Name') == sample_name), None)
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
                                    # opacity=0.01,
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
                                        # bgcolor="rgba(255, 255, 255, 0.8)",
                                        bgcolor=region_colors[region],
                                        bordercolor=region_colors[region],
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
    [Output("download-hmw-data", "data")],
    [
        Input("export-button", "n_clicks"),
    ],
    [
        State("hmw-table", "data"),
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

    # Determine which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_data = json.loads(triggered_id.replace("'", '"'))
        # print(triggered_data)
    except json.JSONDecodeError:
        triggered_data = {}
    # print(triggered_data)
    # **Ensure `report_name` always has a valid value**
    report_name = selected_report
    if 'report_name' in triggered_data:
        report_name = triggered_data['report_name']  # **New report clicked**
    elif isinstance(selected_report, str) and selected_report:  # **Ensure stored report is valid**
        report_name = selected_report

    # **Ensure `report_name` is defined before accessing the database**
    if not report_name:
        print("⚠️ No report found or selected. Returning empty graph.")
        return go.Figure().update_layout(title="No Report Selected"), {'display': 'block'}, selected_report

    # Fetch the selected report
    report = Report.objects.filter(report_id=report_name).first()
    if not report:
        print(f"⚠️ Report '{report_name}' not found in database.")
        return go.Figure().update_layout(title="Report Not Found"), {'display': 'block'}, selected_report

    # Retrieve the list of selected samples
    # selected_result_ids = [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()]
    selected_result_ids = sorted(
        [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()],
        key=lambda x: int(x)  # Assuming result_id is numeric
    )
    # selected_result_ids = sorted(selected_result_ids, key=lambda x: int(x))
    #
    # # Build the sample list by querying SampleMetadata
    # sample_list = []
    # for result_id in selected_result_ids:
    #     sample = SampleMetadata.objects.filter(result_id=result_id).first()
    #     if sample:
    #         sample_list.append(sample.sample_name)

    summary_data = []

    for result_id in selected_result_ids:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            continue

        peak_results = PeakResults.objects.filter(result_id=sample.result_id)
        if not peak_results.exists():
            continue

        df = pd.DataFrame.from_records(peak_results.values())
        # print(df)
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

            # Ensure lmw_end does not exceed low_mw_cutoff
            if lmw_end > low_mw_cutoff:
                lmw_end = low_mw_cutoff

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

            # Limit of detection Calculation
            if total_area > 0:
                peak_area_cutoff = 1000
                if hmw_percent == 100:
                    hmw_percent = f">{round(100 - ((peak_area_cutoff / total_area) * 100), 2)}"
                if main_peak_percent == 100:
                    main_peak_percent = f">{round(100 - ((peak_area_cutoff / total_area) * 100), 2)}"
                if lmw_percent == 100:
                    lmw_percent = f">{round(100 - ((peak_area_cutoff / total_area) * 100), 2)}"

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
                'LMW': lmw_percent,
                'HMW Area': hmw_area,
                'Main Peak Area': main_peak_area,
                'LMW Area': lmw_area
            })

    # Debug the generated summary data
    # print(f"Summary Data: {summary_data}")

    # Define the desired column order
    desired_order = [
        'Sample Name', 'HMW', 'HMW Area', 'HMW Start', 'HMW End',
        'Main Peak', "Main Peak Area", 'Main Peak Start', 'Main Peak End',
        'LMW', 'LMW Area', 'LMW Start', 'LMW End'
    ]

    selected_columns = selected_columns if selected_columns else []
    all_columns = list(set(['Sample Name', 'HMW', 'Main Peak', 'LMW'] + selected_columns))
    ordered_columns = [col for col in desired_order if col in all_columns]

    # Create table columns dynamically
    table_columns = [{"name": col, "id": col} for col in ordered_columns]
    filtered_data = [{col: row[col] for col in ordered_columns if col in row} for row in summary_data]

    return table_columns, filtered_data, summary_data


# Compute the most common peak retention time based on max height
def compute_main_peak_rt(selected_result_ids):
    retention_times = []
    for result_id in selected_result_ids:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            continue

        peak_results = PeakResults.objects.filter(result_id=sample.result_id)
        if not peak_results.exists():
            continue

        df = pd.DataFrame.from_records(peak_results.values())

        # Ensure 'height' and 'peak_retention_time' exist and convert 'height' to numeric
        if df.empty or 'height' not in df.columns or 'peak_retention_time' not in df.columns:
            continue

        df['height'] = pd.to_numeric(df['height'], errors='coerce')  # Convert to numeric, non-numeric -> NaN

        if df['height'].isna().all():  # If all values are NaN, skip this sample
            continue

        max_height_row = df.loc[df['height'].idxmax()]
        retention_times.append(max_height_row['peak_retention_time'])

    return Counter(retention_times).most_common(1)[0][0] if retention_times else 5.10


@app.callback(
    Output("main-peak-rt-input", "value"),  # Store the new RT value
    Input("refresh-rt-btn", "n_clicks"),
    State("selected-report", "data"),
    prevent_initial_call=True
)
def update_main_peak_rt(n_clicks, selected_report):
    if not selected_report:
        print("No report selected.")
        return dash.no_update  # Prevents unnecessary update

    report = Report.objects.filter(report_id=selected_report).first()
    if not report:
        print("Report not found.")
        return dash.no_update
    selected_result_ids = [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()]
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
    if not selected_result_ids:
        print("No samples found in the report.")
        return dash.no_update

    new_rt = compute_main_peak_rt(selected_result_ids)
    print(f"Updated Main Peak RT: {new_rt}")  # Debugging Log

    return new_rt  # This will update `dcc.Store(id="main-peak-rt-store")`


@app.callback(
    [
        Output('time-series-graph', 'figure'),
        Output('time-series-graph', 'style'),
        Output('selected-report', 'data'),
        Output('time-series-graph', 'config')

    ],
    [
        Input('plot-type-dropdown', 'value'),  # Plot type change
        Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),  # Report selection
        Input('shading-checklist', 'value'),
        Input('peak-label-checklist', 'value'),
        Input('main-peak-rt-input', 'value'),
        Input('low-mw-cutoff-input', 'value'),
        Input('regression-parameters', 'data'),
        Input('hmw-table-store', 'data'),
        Input('channel-checklist', 'value'),
        Input('num-cols-input', 'value'),
        Input('vertical-spacing-input', 'value'),
        Input('horizontal-spacing-input', 'value'),
    ],
    [State('selected-report', 'data')],  # Retrieve stored `report_id`
    prevent_initial_call=True
)
def update_graph(plot_type, report_clicks, shading_options, peak_label_options,
                 main_peak_rt, low_mw_cutoff, regression_params, hmw_table_data,
                 selected_channels, num_cols, vertical_spacing, horizontal_spacing,
                 stored_report_id):
    ctx = dash.callback_context

    # ✅ 1. Determine `report_id` from either `ctx.triggered` or `stored_report_id`
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_data = eval(triggered_id)  # Convert string ID to dictionary
    except Exception:
        triggered_data = {}

    report_id = triggered_data.get('report_name') or stored_report_id
    print(f'this is the stored report id {stored_report_id}')

    if not report_id:
        print("⚠️ No report found or selected. Returning empty graph.")
        return go.Figure().update_layout(title="No Report Selected"), {'display': 'block'}, stored_report_id, {}

    # ✅ 2. Fetch the Report using `report_id`
    report = Report.objects.filter(report_id=report_id).first()

    if not report:
        print(f"⚠️ Report '{report_id}' not found in database.")
        return go.Figure().update_layout(title="Report Not Found"), {'display': 'block'}, stored_report_id, {}

    # ✅ 3. Retrieve Sample List and Result IDs
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
    selected_result_ids = [result_id.strip() for result_id in report.selected_result_ids.split(",") if
                           result_id.strip()]
    # Order the result IDs numerically
    selected_result_ids = sorted(selected_result_ids, key=lambda x: int(x))

    # Build the sample list by querying SampleMetadata
    sample_list = []
    for result_id in selected_result_ids:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if sample:
            sample_list.append(sample.sample_name)
    print(f"✅ Report ID: {report_id}")
    print(f"✅ Selected Samples: {sample_list}")
    print(f"✅ Selected Result IDs: {selected_result_ids}")

    current_date = datetime.now().strftime("%Y%m%d")
    filename = f"{current_date}-{report.project_id}-{report.report_name}"

    # ✅ 4. Render Plot Based on Plot Type
    if plot_type == 'plotly':
        fig = go.Figure()
        for result_id in selected_result_ids:
            sample = SampleMetadata.objects.filter(result_id=result_id).first()
            if not sample:
                continue
            time_series = TimeSeriesData.objects.filter(result_id=result_id)
            df = pd.DataFrame(list(time_series.values()))
            for channel in selected_channels:
                if channel in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        name=f"{sample.sample_name} - {channel}"
                    ))

        fig.update_layout(
            title='Time Series Data (Plotly)',
            xaxis_title='Time (Minutes)',
            yaxis_title='UV280',
            template='plotly_white',
            height=800
        )
        return (fig, {'display': 'block'}, report_id,
                {
                    'toImageButtonOptions': {
                        'filename': filename,
                        'format': 'png',
                        # 'height': 600,
                        'width': 800,
                        'scale': 2
                    }})

    elif plot_type == 'subplots':
        if not hmw_table_data:
            print("⚠️ No HMW table data provided.")
            return go.Figure().update_layout(title="No HMW Data"), {'display': 'block'}, report_id

        slope = regression_params.get('slope', 0)
        intercept = regression_params.get('intercept', 0)
        enable_shading = 'enable_shading' in shading_options
        enable_peak_labeling = 'enable_peak_labeling' in peak_label_options

        fig = generate_subplots_with_shading(
            selected_result_ids,
            sample_list,
            selected_channels,
            enable_shading=enable_shading,
            enable_peak_labeling=enable_peak_labeling,
            main_peak_rt=main_peak_rt,
            slope=slope,
            intercept=intercept,
            hmw_table_data=hmw_table_data,
            num_cols=num_cols,
            vertical_spacing=vertical_spacing,
            horizontal_spacing=horizontal_spacing
        )

        return (fig, {'display': 'block'}, report_id,
                {
                    'toImageButtonOptions': {
                        'filename': filename,
                        'format': 'png',
                        # 'height': 600,
                        # 'width': 800,
                        'scale': 2
                    }})

    return go.Figure(), {'display': 'block'}, report_id, {}
