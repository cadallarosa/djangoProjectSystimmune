# from dash import dcc, html
# import plotly.graph_objs as go
# import pandas as pd
# from dash.dependencies import Input, Output
# from django_plotly_dash import DjangoDash
# from .models import SampleMetadata, TimeSeriesData
# import plotly.express as px
#
# # Initialize Dash app
# app = DjangoDash('TimeSeriesPlot')
#
# app.layout = html.Div([
#     html.Div([
#         dcc.Input(
#             id='sample_name_input',
#             type='text',
#             placeholder='Enter sample name or range (e.g., S1-S5)',
#             style={'width': '300px'}
#         ),
#         html.Button('Submit', id='submit_button', n_clicks=0),
#     ], style={'margin-bottom': '20px'}),
#
#     dcc.Checklist(
#         id='channel_selection',
#         options=[
#             {'label': 'Channel 1', 'value': 'channel_1'},
#             {'label': 'Channel 2', 'value': 'channel_2'},
#             {'label': 'Channel 3', 'value': 'channel_3'},
#         ],
#         value=['channel_1', 'channel_2', 'channel_3'],
#         labelStyle={'display': 'inline-block', 'margin-right': '10px'}
#     ),
#
#     dcc.Graph(id='time_series_plot')
# ])
#
# @app.callback(
#     Output('time_series_plot', 'figure'),
#     Input('submit_button', 'n_clicks'),
#     Input('sample_name_input', 'value'),
#     Input('channel_selection', 'value')
# )
# @app.callback(
#     Output('time_series_plot', 'figure'),
#     Input('submit_button', 'n_clicks'),
#     Input('sample_name_input', 'value'),
#     Input('channel_selection', 'value')
# )
# def update_graph(n_clicks, sample_name_range, selected_channels):
#     print(f"Sample Name Range: {sample_name_range}")
#     print(f"Selected Channels: {selected_channels}")
#
#     # Ensure a click has been made and that inputs are valid
#     if n_clicks == 0 or not sample_name_range or not selected_channels:
#         return go.Figure()
#
#     # Retrieve samples based on the input
#     if '-' in sample_name_range:
#         start, end = sample_name_range.split('-')
#         samples = SampleMetadata.objects.filter(sample_name__range=(start, end))
#     else:
#         samples = SampleMetadata.objects.filter(sample_name=sample_name_range)
#
#     # Initialize the figure
#     fig = go.Figure()
#
#     # Loop over samples and add traces
#     for sample in samples:
#         time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
#         df = pd.DataFrame(list(time_series.values()))
#         print(f"DataFrame size for {sample.sample_name}: {df.shape}")
#
#         # if 'time' in df.columns:
#         #     df['time'] = pd.to_datetime(df['time'])
#         # else:
#         #     print(f"No 'time' column for sample {sample.sample_name}")
#         #     continue
#
#         # Add traces for each selected channel
#         for channel in selected_channels:
#             if channel in df.columns:
#                 fig.add_trace(go.Scatter(
#                     x=df['time'],
#                     y=df[channel],
#                     mode='lines',
#                     name=f"{sample.sample_name} - {channel}"
#                 ))
#             else:
#                 print(f"Channel '{channel}' not found for sample {sample.sample_name}")
#
#     # If no data was added to the figure, return a figure with a message
#     if not fig.data:
#         return go.Figure().update_layout(title='No data found for the selected channels.')
#
#     # Log the figure's data for debugging
#     print(f"Figure data: {fig.data}")
#     print(f"Figure layout: {fig.layout}")
#
#     # Update figure layout
#     fig.update_layout(
#         title='Time Series Data',
#         xaxis_title='Time',
#         yaxis_title='Intensity',
#         template='plotly_white'
#     )
#
#     return fig
#

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

