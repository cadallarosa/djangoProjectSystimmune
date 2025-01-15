import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django_plotly_dash import DjangoDash
import dash
from dash import dcc, html, Input, Output, State, dash_table, Dash
import pandas as pd
from .models import Report, SampleMetadata, PeakResults, TimeSeriesData
import json
import logging
from openpyxl.workbook import Workbook

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
    dcc.Store(id='selected-report', data=None),

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
                                {'label': 'Channel 1', 'value': 'channel_1'},
                                {'label': 'Channel 2', 'value': 'channel_2'}
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
                            value=[],  # Default to off
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

                        dcc.Checklist(
                            id='peak-label-checklist',
                            options=[
                                {'label': 'Enable Peak Labeling', 'value': 'enable_peak_labeling'}
                            ],
                            value=[],  # Default to no peak labeling
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
                    # 'margin': '10px',
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
                    html.Div(
                        id='sample-details-content',
                        children=[
                            html.P("Sample Set Name: ", id="sample-set-name"),
                            html.P("Column Name: ", id="column-name"),
                            html.P("Column Serial Number: ", id="column-serial-number"),
                            html.P("Instrument Method Name: ", id="instrument-method-name"),
                            html.P("STD ID: ", id="standard-id"),
                        ],
                        style={
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc',
                        }
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
                            dcc.Graph(id='regression-plot', style={'margin-top': '20px'})
                        ],
                        style={
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc',
                        }
                    )
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


# Set up logging to log to a file
logging.basicConfig(filename='app_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def generate_subplots_with_shading(sample_list, channels, enable_shading, enable_peak_labeling, main_peak_rt):
    num_samples = len(sample_list)
    cols = 2
    rows = (num_samples // cols) + (num_samples % cols > 0)

    region_colors = {
        "HMW": "red",  # Light blue
        "MP": "blue",  # Light green
        "LMW": "green"  # Light yellow
    }

    label_offsets = {
        "HMW": {"x_offset": -0.5, "y_offset": 1},  # Offset left and above
        "MP": {"x_offset": 0, "y_offset": 0.05},  # Centered above the peak
        "LMW": {"x_offset": 0.1, "y_offset": 1}  # Offset right and above
    }

    fig = make_subplots(
        rows=rows,
        cols=cols,
        start_cell="top-left",
        subplot_titles=sample_list,
        vertical_spacing=0.05,
        horizontal_spacing=0.05
    )

    for i, sample_name in enumerate(sample_list):
        row = (i // cols) + 1
        col = (i % cols) + 1
        sample = SampleMetadata.objects.filter(sample_name=sample_name).first()
        if not sample:
            continue
        time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
        peak_results = PeakResults.objects.filter(result_id=sample.result_id)

        df = pd.DataFrame(list(time_series.values()))
        peaks_df = pd.DataFrame(list(peak_results.values()))

        for channel in channels:
            if channel in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        line=dict(color="blue"),
                        name=f"{sample_name} - {channel}",
                        # hoverinfo = "x+y+name"
                    ),
                    row=row,
                    col=col
                )

                if enable_shading and 'peak_retention_time' in peaks_df.columns and 'percent_area' in peaks_df.columns:
                    peaks_df['peak_retention_time'] = peaks_df['peak_retention_time'].astype(float)
                    peaks_df['percent_area'] = peaks_df['percent_area'].astype(float)

                    closest_index = (peaks_df['peak_retention_time'] - main_peak_rt).abs().idxmin()
                    main_peak_start = peaks_df.loc[closest_index, 'peak_start_time']
                    main_peak_end = peaks_df.loc[closest_index, 'peak_end_time']

                    hmw_start = peaks_df[peaks_df['peak_retention_time'] < main_peak_start]['peak_start_time'].min()
                    hmw_end = main_peak_start
                    lmw_start = main_peak_end
                    lmw_end = peaks_df[peaks_df['peak_retention_time'] > main_peak_end]['peak_end_time'].max()

                    shading_regions = {
                        "HMW": (hmw_start, hmw_end),
                        "MP": (main_peak_start, main_peak_end),
                        "LMW": (lmw_start, lmw_end)
                    }

                    percentages = {
                        "HMW": round(peaks_df[peaks_df['peak_retention_time'] < main_peak_start]['percent_area'].sum(),
                                     2) if pd.notna(hmw_start) else 0,
                        "MP": round(peaks_df.loc[closest_index, 'percent_area'], 2) if closest_index is not None else 0,
                        "LMW": 0
                    }

                    if percentages["HMW"] + percentages["MP"] <= 100:
                        percentages["LMW"] = round(100 - percentages["HMW"] - percentages["MP"], 2)

                    for region, (start_time, end_time) in shading_regions.items():
                        if pd.notna(start_time) and pd.notna(end_time):
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

                        if enable_peak_labeling and region in percentages:
                            if pd.notna(start_time) and pd.notna(end_time):
                                shading_region = df[(df['time'] >= start_time) & (df['time'] <= end_time)]
                                if not shading_region.empty:
                                    peak_value = shading_region[channel].max()
                                    peak_time = shading_region[shading_region[channel] == peak_value]['time'].values[0]

                                    x_offset = label_offsets[region]["x_offset"] * (
                                            shading_region['time'].max() - shading_region['time'].min())
                                    y_offset = label_offsets[region]["y_offset"] * peak_value

                                    fig.add_annotation(
                                        x=peak_time + x_offset,
                                        y=peak_value + y_offset + 0.01,
                                        text=f"{region}: {percentages[region]}%",
                                        showarrow=False,
                                        font=dict(size=14, color="black"),
                                        align="center",
                                        row=row,
                                        col=col
                                    )

        # Add X-axis and Y-axis labels for each subplot
        fig.update_xaxes(
            title_text="Time (min)",
            title_standoff=3,  # Reduce padding (default is larger, e.g., 20)
            row=row,
            col=col
        )
        fig.update_yaxes(
            title_text="UV280",
            title_standoff=3,  # Reduce padding (default is larger, e.g., 20)
            row=row,
            col=col
        )
    fig.update_layout(
        height=350 * rows,
        margin=dict(l=10, r=10, t=50, b=10),
        title="Sample Subplots with Shading and Labels",
        title_x=0.5,
        showlegend=False,
        plot_bgcolor="white"
    )

    for i in range(1, rows * cols + 1):
        fig['layout'][f'xaxis{i}'].update(showgrid=False, zeroline=False)
        fig['layout'][f'yaxis{i}'].update(showgrid=False, zeroline=False)

    return fig


@app.callback(
    [Output('time-series-graph', 'figure'),
     Output('time-series-graph', 'style'),
     Output('selected-report', 'data')],
    [Input('plot-type-dropdown', 'value'),
     Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),
     Input('shading-checklist', 'value'),
     Input('peak-label-checklist', 'value'),
     Input('main-peak-rt-input', 'value')],
    [State('selected-report', 'data'),
     State('channel-checklist', 'value')],
    prevent_initial_call=True
)
def update_graph(plot_type, report_clicks, shading_options, peak_label_options, main_peak_rt, selected_report,
                 selected_channels):
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
            height=400
        )
        return fig, {'display': 'block'}, report_name  # Show Plotly graph and persist report


    elif plot_type == 'subplots':

        enable_shading = 'enable_shading' in shading_options

        enable_peak_labeling = 'enable_peak_labeling' in peak_label_options

        fig = generate_subplots_with_shading(sample_list, selected_channels, enable_shading, enable_peak_labeling,
                                             main_peak_rt)

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


from django.db.models import F, ExpressionWrapper, fields


@app.callback(
    [
        Output("sample-set-name", "children"),
        Output("column-name", "children"),
        Output("column-serial-number", "children"),
        Output("instrument-method-name", "children"),
        Output("standard-id", "children")
    ],
    Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_sample_and_std_details(report_clicks):
    ctx = dash.callback_context

    # Default return values
    default_values = (
        "Sample Set Name: ",
        "Column Name: ",
        "Column Serial Number: ",
        "Instrument Method Name: ",
        "STD ID: "
    )

    if not ctx.triggered:
        return default_values

    # Determine the triggering report
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_data = eval(triggered_id)

    if 'report_name' not in triggered_data:
        return default_values

    report_name = triggered_data['report_name']
    report = Report.objects.filter(report_name=report_name).first()

    if not report:
        return default_values

    # Fetch the first sample name from the report's selected samples
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
    if not sample_list:
        return default_values

    first_sample_name = sample_list[0]
    sample_metadata = SampleMetadata.objects.filter(sample_name=first_sample_name).first()

    if not sample_metadata:
        return default_values

    # Extract details from the `SampleMetadata` model
    sample_set_name = sample_metadata.sample_set_name or "N/A"
    column_name = sample_metadata.column_name or "N/A"
    column_serial_number = sample_metadata.column_serial_number or "N/A"
    system_name = sample_metadata.system_name or "N/A"
    instrument_method_name = sample_metadata.instrument_method_name or "N/A"
    sample_date_acquired = sample_metadata.date_acquired

    # Primary STD search: Check for an STD in the same sample set
    std_sample = SampleMetadata.objects.filter(
        sample_set_name='241210 98x2 FB1339_1348 2Wks', sample_prefix="STD"
    ).first()

    # Secondary STD search: Simplified to ensure results
    if not std_sample:
        std_sample = (
            SampleMetadata.objects.filter(
                sample_prefix="STD "  # Only filter by sample_prefix for now
            )

        )

    # Determine the STD ID or fallback value
    std_result_id = std_sample.result_id if std_sample else "No STD Found"

    # Debug output
    print(f"STD Result: {std_sample}")
    print(f"STD Result ID: {std_result_id}")

    # Return formatted details for display
    return (
        f"Sample Set Name: {sample_set_name}",
        f"Column Name: {column_name}",
        f"Column Serial Number: {column_serial_number}",
        f"Instrument Method Name: {instrument_method_name}",
        f"STD Result ID: {std_result_id}"
    )


import pandas as pd
import numpy as np


@app.callback(
    [
        Output("regression-equation", "children"),
        Output("r-squared-value", "children"),
        Output("regression-plot", "figure"),
        Output("estimated-mw", "children")
    ],
    [
        Input("calculate-mw-button", "n_clicks"),
        State("rt-input", "value"),
        State("standard-id", "children")  # Get the STD ID
    ],
    prevent_initial_call=True
)
def standard_analysis(n_clicks, rt_input, standard_id):
    from scipy.stats import linregress
    import plotly.graph_objects as go

    # Extract the STD ID from the input (remove the label prefix)
    std_result_id = 36704
    if std_result_id == "N/A":
        return "No STD Selected", "N/A", {}, "N/A"

    # Query the PeakResults table for the given STD result ID
    peak_results = PeakResults.objects.filter(result_id=std_result_id).values(
        "peak_name", "peak_retention_time", "area", "percent_area"
    )

    # Convert query results to a DataFrame
    df = pd.DataFrame(list(peak_results))
    print(df)
    if df.empty:
        return "No Peak Results Found", "N/A", {}, "N/A"

    # Map MW values using the provided dictionary
    new_data = {
        'Peak1-Thyroglobulin': 1400000,
        'Peak2- Thyroglobulin': 660000,
        'Peak3-IgG': 150000,
        'Peak4-BSA': 66400,
        'Peak5-Myoglobin': 17000,
        'Peak7-Uracil': 112
    }
    df["MW"] = df["peak_name"].map(new_data)

    # Sort the DataFrame by peak retention time
    df = df.sort_values(by="peak_retention_time").reset_index(drop=True)

    # Ensure Log(MW) column for linear regression
    df["Log_MW"] = df["MW"].apply(lambda x: np.log(x) if pd.notnull(x) else None)

    # Perform linear regression
    regression_data = df.dropna(subset=["Log_MW", "peak_retention_time"])
    slope, intercept, r_value, _, _ = linregress(
        regression_data["peak_retention_time"], regression_data["Log_MW"]
    )

    # Regression equation and R² value
    regression_equation = f"y = {slope:.4f}x + {intercept:.4f}"
    r_squared = f"R² = {r_value ** 2:.4f}"

    # Generate the regression plot
    x_vals = np.linspace(
        regression_data["peak_retention_time"].min(),
        regression_data["peak_retention_time"].max(),
        100
    )
    y_vals = slope * x_vals + intercept

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=regression_data["peak_retention_time"],
        y=regression_data["Log_MW"],
        mode="markers",
        name="Data Points"
    ))
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals, mode="lines", name="Regression Line"
    ))
    fig.update_layout(
        title="Retention Time vs Log(MW) with Linear Regression",
        xaxis_title="Retention Time",
        yaxis_title="Log(MW)",
        template="plotly_white"
    )

    # Calculate MW for the provided retention time input
    estimated_mw = "N/A"
    if rt_input is not None:
        log_mw = slope * rt_input + intercept
        estimated_mw = f"Estimated MW: {np.exp(log_mw) / 1000:.4f} kD"

    return regression_equation, r_squared, fig, estimated_mw
