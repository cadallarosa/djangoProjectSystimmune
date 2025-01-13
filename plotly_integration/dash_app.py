import plotly.graph_objs as go
from django_plotly_dash import DjangoDash
import dash
from dash import dcc, html, Input, Output, State, dash_table, Dash
import plotly.graph_objects as go
import pandas as pd
from .models import Report, SampleMetadata, PeakResults, TimeSeriesData

# Initialize the Dash app
app = DjangoDash('TimeSeriesApp')

# Fetch available projects and reports
projects = {}
for report in Report.objects.all():
    if report.project_id not in projects:
        projects[report.project_id] = []
    projects[report.project_id].append({'name': report.report_name, 'samples': report.selected_samples})


# Sidebar content generator
def generate_sidebar(projects):
    sidebar_items = [
        html.Div("Projects", style={
            'text-align': 'center',
            'margin-bottom': '20px',
            'font-weight': 'bold',
            'font-size': '18px',
            'color': '#0056b3'
        }),
        html.P("Right-click on the results to change the report", style={
            'font-size': '12px',
            'color': '#555',
            'text-align': 'center'
        }),
    ]

    for project_id, reports in projects.items():
        project_folder = html.Div([
            html.Div(
                f"📁 Project {project_id}",
                className="folder",
                id={'type': 'folder', 'project_id': project_id},
                n_clicks=0,
                style={
                    'cursor': 'pointer',
                    'margin-bottom': '10px',
                    'font-weight': 'bold',
                    'color': '#0056b3',
                    'padding': '5px',
                    'border': '1px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#e9f1fb'
                }
            ),
            html.Div(
                [html.Div([
                    html.Div(f"📄 {report['name']}", style={'font-weight': 'bold', 'color': '#0056b3'}),
                    html.Div(f"Samples: {report['samples']}", style={
                        'font-size': '12px',
                        'color': '#555',
                        'margin-left': '10px'
                    })
                ],
                    className="report",
                    id={'type': 'report', 'report_name': report['name']},
                    style={
                        'border': '1px solid #ccc',
                        'padding': '10px',
                        'margin-bottom': '5px',
                        'background-color': '#f9f9f9',
                        'cursor': 'pointer',
                        'border-radius': '5px'
                    }
                ) for report in reports],
                className="folder-contents",
                style={'display': 'none', 'margin-left': '10px'},
                id={'type': 'contents', 'project_id': project_id}
            )
        ])
        sidebar_items.append(project_folder)
    return sidebar_items


# Layout for the Dash app
app.layout = html.Div([
    # Top-left Home Button
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
            children=generate_sidebar(projects),
            style={
                'width': '20%',
                'height': 'calc(100vh - 50px)',
                'background-color': '#f7f7f7',
                'padding': '10px',
                'overflow-y': 'auto',
                'border-right': '1px solid #ccc',
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
                    'padding': '10px',
                    'background-color': '#e9ecef',
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
                                    yaxis_title="UV280"
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
                                {'label': 'Select Channel', 'value': 'channel_1'},
                                {'label': 'Select Plot Type', 'value': 'channel_2'}
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
                        html.P("Shade Areas"),
                        html.P("Estimated Size"),
                        html.P("Peak Retention Time"),
                    ],
                    style={
                        'width': '30%',
                        'padding': '10px',
                        'background-color': '#f7f9fc',
                        'border-left': '2px solid #0056b3',
                        'border-radius': '5px'
                    }
                )
            ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'}),
            html.Div(  # HMW Data area
                id='hmw-data',
                children=[
                    html.H4("Peak Results", style={'text-align': 'center', 'color': '#0056b3'}),
                    dash_table.DataTable(
                        id='hmw-table',
                        columns=[
                            {"name": "Sample Name", "id": "Sample Name"},
                            {"name": "HMW", "id": "HMW"},
                            {"name": "Main Peak", "id": "Main Peak"},
                            {"name": "LMW", "id": "LMW"}
                        ],
                        data=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'center', 'padding': '5px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                    )
                ],
                style={
                    # 'margin': '10px',
                    'width': '68%',
                    'padding': '10px',
                    'border': '2px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#f7f9fc'
                }
            )
        ], style={'width': '80%', 'padding': '10px', 'overflow-y': 'auto'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'})
])


# Callbacks for folder toggle functionality
@app.callback(
    Output({'type': 'contents', 'project_id': dash.dependencies.ALL}, 'style'),
    Input({'type': 'folder', 'project_id': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def toggle_folder(n_clicks_list):
    styles = [{'display': 'none'} if not n_clicks or n_clicks % 2 == 0 else {'display': 'block'} for n_clicks in
              n_clicks_list]
    return styles


import logging

# Set up logging to log to a file
logging.basicConfig(filename='app_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

from plotly.subplots import make_subplots
import plotly.graph_objects as go


def generate_subplots(sample_list, channels):
    num_samples = len(sample_list)
    cols = 4  # Number of columns in the subplot grid
    rows = (num_samples // cols) + (num_samples % cols > 0)

    # Create a subplot figure
    fig = make_subplots(rows=rows, cols=cols, start_cell="top-left")

    # Populate subplots with data
    for i, sample_name in enumerate(sample_list):
        row = (i // cols) + 1
        col = (i % cols) + 1
        sample = SampleMetadata.objects.filter(sample_name=sample_name).first()
        if not sample:
            continue
        time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
        df = pd.DataFrame(list(time_series.values()))

        for channel in channels:
            if channel in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        name=f"{sample_name} - {channel}"
                    ),
                    row=row,
                    col=col
                )

    # Update the layout
    fig.update_layout(
        height=400 * rows,  # Dynamically adjust height based on rows
        title="Sample Subplots",
        showlegend=False,
    )
    return fig


import json


@app.callback(
    [Output('time-series-graph', 'figure'),
     Output('time-series-graph', 'style'),
     Output('selected-report', 'data')],  # Persist the selected report
    [Input('plot-type-dropdown', 'value'),
     Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks')],
    [State('selected-report', 'data'),
     State('channel-checklist', 'value')],
    prevent_initial_call=True
)
def update_graph(plot_type, report_clicks, selected_report, selected_channels):
    ctx = dash.callback_context

    # If no trigger, return an empty figure
    if not ctx.triggered or not selected_channels:
        return go.Figure(), {'display': 'block'}, selected_report

    # Determine the triggered input
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_name = None

    if 'report_name' in triggered_id:  # If a report was selected
        triggered_data = eval(triggered_id)
        report_name = triggered_data.get('report_name', None)
    elif selected_report:  # Use the stored report if switching modes
        report_name = selected_report.get('report_name', None)

    if not report_name:
        return go.Figure().update_layout(title="No Report Selected"), {'display': 'block'}, selected_report

    # Fetch the report from the database
    report = Report.objects.filter(report_name=report_name).first()
    if not report:
        return go.Figure(), {'display': 'block'}, selected_report

    # Parse the selected samples from the report
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]

    if plot_type == 'plotly':
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

        fig.update_layout(
            title='Time Series Data',
            xaxis_title='Time',
            yaxis_title='UV280',
            template='plotly_white',
            height=400
        )
        return fig, {'display': 'block'}, {'report_name': report_name}

    elif plot_type == 'subplots':
        fig = generate_subplots(sample_list, selected_channels)
        return fig, {'display': 'block'}, {'report_name': report_name}


@app.callback(
    Output('hmw-table', 'data'),
    Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_hmw_table(report_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        return []

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_data = eval(triggered_id)

    if 'report_name' not in triggered_data:
        return []

    report_name = triggered_data['report_name']
    report = Report.objects.filter(report_name=report_name).first()

    if not report:
        return []

    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
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

        if 'peak_retention_time' not in df.columns or 'percent_area' not in df.columns:
            continue

        df['peak_retention_time'] = df['peak_retention_time'].astype(float)
        df['percent_area'] = df['percent_area'].astype(float)

        main_peak_rt = 5.10
        closest_index = (df['peak_retention_time'] - main_peak_rt).abs().idxmin()
        main_peak_area = round(df.loc[closest_index, 'percent_area'], 2)

        hmw_value = round(df[df['peak_retention_time'] < main_peak_rt]['percent_area'].sum(), 2)
        lmw_value = round(100 - hmw_value - main_peak_area, 2)

        summary_data.append({
            'Sample Name': sample.sample_name,
            'HMW': hmw_value,
            'Main Peak': main_peak_area,
            'LMW': lmw_value
        })

    return summary_data
