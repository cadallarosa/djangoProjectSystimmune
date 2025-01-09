from dash import dcc, html, Dash
import plotly.graph_objs as go
import pandas as pd
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from .models import SampleMetadata, TimeSeriesData
import plotly.express as px

# views.py
from django.shortcuts import render
import plotly.graph_objects as go
import pandas as pd
from .models import SampleMetadata, TimeSeriesData


def plot_time_series(request):
    # Sample name and channel selection
    sample_name_range = 'PD2360'  # Modify this as per user input
    selected_channels = ['channel_1', 'channel_2', 'channel_3']  # Modify this as per user input

    # Retrieve samples based on the input (adjust as necessary)
    if '-' in sample_name_range:
        start, end = sample_name_range.split('-')
        samples = SampleMetadata.objects.filter(sample_name__range=(start, end))
    else:
        samples = SampleMetadata.objects.filter(sample_name=sample_name_range)

    # Initialize the figure
    fig = go.Figure()

    # Loop over samples and add traces
    for sample in samples:
        time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
        df = pd.DataFrame(list(time_series.values()))

        # Assuming 'time' column is in seconds (no need to convert to datetime)
        if 'time' in df.columns:
            df['time'] = pd.to_timedelta(df['time'], unit='s')
        else:
            continue  # Skip if 'time' column is missing

        # Add traces for each selected channel
        for channel in selected_channels:
            if channel in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df[channel],
                    mode='lines',
                    name=f"{sample.sample_name} - {channel}"
                ))

    # Update layout
    fig.update_layout(
        title='Time Series Data',
        xaxis_title='Time (seconds)',
        yaxis_title='Intensity',
        xaxis=dict(tickformat='%H:%M:%S'),  # Format as hours:minutes:seconds
        template='plotly_white'
    )

    # Convert the plot to HTML for rendering
    plot_html = fig.to_html(full_html=False)

    # Pass the plot HTML to the template
    return render(request, 'your_template.html', {'plot_html': plot_html})


import dash
from dash import html, dcc
import plotly.express as px
import pandas as pd
from django_plotly_dash import DjangoDash

import logging

# Set up logging for debugging
logger = logging.getLogger(__name__)

# Initialize Dash app
app = DjangoDash('TimeSeriesPlot123')

# Define layout
app.layout = html.Div([
    html.Div([
        dcc.Input(
            id='sample_name_input',
            type='text',
            placeholder='Enter sample name or range (e.g., S1-S5)',
            style={'width': '300px'}
        ),
        html.Button('Submit', id='submit_button', n_clicks=0),
    ], style={'margin-bottom': '20px'}),

    dcc.Checklist(
        id='channel_selection',
        options=[
            {'label': 'Channel 1', 'value': 'channel_1'},
            {'label': 'Channel 2', 'value': 'channel_2'},
            {'label': 'Channel 3', 'value': 'channel_3'},
        ],
        value=['channel_1', 'channel_2', 'channel_3'],
        labelStyle={'display': 'inline-block', 'margin-right': '10px'}
    ),

    dcc.Graph(
        id='time_series_plot',
        figure=go.Figure().update_layout(title='Waiting for input...')
    )
])


# Define callback for updating the graph
@app.callback(
    Output('time_series_plot', 'figure'),
    Input('submit_button', 'n_clicks'),
    Input('sample_name_input', 'value'),
    Input('channel_selection', 'value')
)
def update_graph(n_clicks, sample_name_range, selected_channels):
    # Return an empty figure if no input is provided
    if n_clicks == 0 or not sample_name_range or not selected_channels:
        logger.info("Returning empty figure due to missing inputs.")
        return go.Figure().update_layout(title='Waiting for valid inputs.')

    try:
        # Parse the sample name range
        if '-' in sample_name_range:
            start, end = sample_name_range.split('-')
            samples = SampleMetadata.objects.filter(sample_name__range=(start.strip(), end.strip()))
        else:
            samples = SampleMetadata.objects.filter(sample_name=sample_name_range.strip())
    except ValueError:
        logger.error("Invalid sample range.")
        return go.Figure().update_layout(title='Invalid sample range')

    fig = go.Figure()

    # Process data for each sample
    for sample in samples:
        time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
        df = pd.DataFrame(list(time_series.values()))

        if 'time' in df.columns:
            # Convert 'time' column to datetime and handle invalid times
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            df = df.dropna(subset=['time'])

            # Add traces for each selected channel
            for channel in selected_channels:
                if channel in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        name=f"{sample.sample_name} - {channel}"
                    ))

    # Handle case with no data
    if not fig.data:
        logger.info("No data found for the selected channels.")
        return go.Figure().update_layout(title='No data found for the selected channels.')

    # Update figure layout
    fig.update_layout(
        title='Time Series Data',
        xaxis_title='Time',
        yaxis_title='Intensity',
        template='plotly_white'
    )

    logger.info(f"Returning figure with {len(fig.data)} traces.")
    return fig


from dash import dcc, html  # Modern import
import plotly.express as px
import pandas as pd

# Sample data
df = pd.DataFrame({
    "Category": ["A", "B", "C", "A", "B", "C", "A", "B", "C"],
    "Value": [10, 15, 20, 25, 30, 35, 40, 45, 50]
})

fig = px.bar(df, x="Category", y="Value")

app = DjangoDash('TimeSeriesPlot1234')

app.layout = html.Div(
    style={
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
        "justifyContent": "center",
        "width": "100%",
        "height": "100vh",  # Take up full viewport height
        "backgroundColor": "#f4f7f6",  # Soft background color for a sleek look
        "fontFamily": "Arial, sans-serif",  # Sleek font
    },
    children=[
        html.H1(
            "Responsive Dash App with Filters",
            style={
                "textAlign": "center",
                "marginBottom": "20px",
                "color": "#333",  # Darker text color for better contrast
            }
        ),

        # Buttons to filter data (using html.Button now)
        html.Div(
            children=[
                html.Button("Show Category A", id="btn-a", n_clicks=0, className="filter-btn"),
                html.Button("Show Category B", id="btn-b", n_clicks=0, className="filter-btn"),
                html.Button("Show Category C", id="btn-c", n_clicks=0, className="filter-btn"),
                html.Button("Show All", id="btn-all", n_clicks=0, className="filter-btn"),  # New Show All button
            ],
            style={
                "display": "flex",
                "justifyContent": "center",
                "gap": "10px",  # Spacing between buttons
                "marginBottom": "20px",
            }
        ),

        # Graph that will update based on button clicks
        dcc.Graph(
            id="example-graph",
            figure=fig,
            style={
                "width": "80%",  # Reduced width for a cleaner look
                "height": "80%",  # Reduced height to fit the page better
                "maxWidth": "900px",  # Max width to prevent excessive stretching
                "marginBottom": "40px",  # Margin for space at the bottom
            },
            config={"responsive": True},  # Ensure the graph is responsive
        ),
    ]
)


# Callback to update the figure based on button clicks
@app.callback(
    dash.dependencies.Output("example-graph", "figure"),
    [dash.dependencies.Input("btn-a", "n_clicks"),
     dash.dependencies.Input("btn-b", "n_clicks"),
     dash.dependencies.Input("btn-c", "n_clicks"),
     dash.dependencies.Input("btn-all", "n_clicks")],  # Include the Show All button
)
def update_graph(btn_a, btn_b, btn_c, btn_all):
    ctx = dash.callback_context

    # Check which button was clicked
    if not ctx.triggered:
        return fig  # Default figure (no filter)
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "btn-a":
        # Filter for Category A
        filtered_df = df[df["Category"] == "A"]
    elif button_id == "btn-b":
        # Filter for Category B
        filtered_df = df[df["Category"] == "B"]
    elif button_id == "btn-c":
        # Filter for Category C
        filtered_df = df[df["Category"] == "C"]
    elif button_id == "btn-all":
        # Show all data
        filtered_df = df
    else:
        filtered_df = df  # Show all data if no filter is selected

    # Create a new figure based on filtered data
    return px.bar(filtered_df, x="Category", y="Value")


# Add CSS for styling buttons
app.css.append_css({
    'external_url': 'https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap'
})

import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
from django_plotly_dash import DjangoDash
from .models import Report

# Initialize the Dash app
app = DjangoDash('TimeSeriesApp')

# Fetch available projects and reports
projects = {}
for report in Report.objects.all():
    if report.project_id not in projects:
        projects[report.project_id] = []
    projects[report.project_id].append({'name': report.report_name, 'samples': report.selected_samples})

# Dummy HMW data
hmw_data = pd.DataFrame({
    "Sample Name": ["Sample 1", "Sample 2", "Sample 3"],
    "HMW": [10, 15, 20],
    "Main": [70, 60, 55],
    "LMW": [20, 25, 25]
})

# Dummy plot data
dummy_time_series_data = {
    "Sample Name": ["Sample 1", "Sample 2", "Sample 3"],
    "Time": [1, 2, 3],
    "Value": [10, 15, 20]
}

dummy_time_series_data2 = {
    "Sample Name": ["Sample 1", "Sample 2", "Sample 3"],
    "Time": [1, 2, 3, 4],
    "Value": [10, 15, 20, 50]
}


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
                html.Div(  # Plot area
                    id='plot-area',
                    children=[
                        html.H4("Plot", style={'text-align': 'center', 'color': '#0056b3'}),
                        dcc.Graph(
                            id='time-series-graph',
                            figure=go.Figure(
                                data=[go.Scatter(
                                    x=dummy_time_series_data["Time"],
                                    y=dummy_time_series_data["Value"],
                                    mode='lines+markers'
                                )],
                                layout=go.Layout(
                                    title="Sample Plot",
                                    xaxis_title="Time",
                                    yaxis_title="Value"
                                )
                            )
                        )
                    ],
                    style={
                        'width': '70%',
                        'padding': '10px',
                        'border': '1px solid #0056b3',
                        'border-radius': '5px',
                        'background-color': '#f7f9fc'
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
                        html.P("Shade Areas"),
                        html.P("Estimated Size"),
                        html.P("Peak Retention Time")
                    ],
                    style={
                        'width': '30%',
                        'padding': '10px',
                        'background-color': '#f7f9fc',
                        'border-left': '1px solid #0056b3',
                        'border-radius': '5px'
                    }
                )
            ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'}),
            html.Div(  # HMW Data area
                id='hmw-data',
                children=[
                    html.H4("HMW Data", style={'text-align': 'center', 'color': '#0056b3'}),
                    dash_table.DataTable(
                        id='hmw-table',
                        columns=[{"name": col, "id": col} for col in hmw_data.columns],
                        data=hmw_data.to_dict('records'),
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'center', 'padding': '5px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                    )
                ],
                style={
                    'margin': '10px',
                    'padding': '10px',
                    'border': '1px solid #0056b3',
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


@app.callback(
    Output('time-series-graph', 'figure'),
    Input({'type': 'report', 'report_name': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_graph(n_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        return go.Figure()  # Default figure

    # Get the triggered report name from the ID
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_data = eval(triggered_id)  # Convert string back to dictionary

    if 'report_name' in triggered_data:
        report_name = triggered_data['report_name']
        print("Triggered Report Name:", report_name)  # Debugging output
    else:
        report_name = None

    if not report_name:
        return go.Figure().update_layout(title="Invalid Report Name")
    selected_report = report_name
    print(selected_report)

    # Fetch the report
    report = Report.objects.filter(report_name=selected_report).first()
    if not report:
        return go.Figure()  # Return an empty figure if the report is not found

    # Parse the selected samples from the report
    selected_samples = report.selected_samples
    sample_list = [sample.strip() for sample in selected_samples.split(",") if sample.strip()]
    print(sample_list)
    if not sample_list:
        return go.Figure()  # Return an empty figure if there are no samples

        # Proceed with the plotting logic if sample_list is populated
    if sample_list:
        sample_names = sample_list
        selected_channels = ['channel_1']  # Modify as needed
        filtered_samples = SampleMetadata.objects.filter(sample_name__in=sample_names)

        # Initialize the figure
        fig = go.Figure()

        # Loop over samples and add traces
        for sample in filtered_samples:
            time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
            df = pd.DataFrame(list(time_series.values()))

            # Add traces for each selected channel
            for channel in selected_channels:
                if channel in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        name=f"{sample.sample_name} - {channel}"
                    ))

        # Update layout
        fig.update_layout(
            title='Time Series Data',
            xaxis_title='Time (seconds)',
            yaxis_title='Intensity',
            template='plotly_white'
        )

    return fig
