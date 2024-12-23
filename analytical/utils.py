import matplotlib.pyplot as plt
from io import BytesIO
from django.http import HttpResponse
from .models import SampleMetadata, SystemInformation, TimeSeriesData  # Assuming models are imported
import pandas as pd


def query_system_information(system_name):
    """
    Query the system information from the database using the system name.
    Replace this with the actual Django ORM query.
    """
    try:
        system_info = SystemInformation.objects.get(system_name=system_name)
        return system_info.channel_1, system_info.channel_2, system_info.channel_3
    except SystemInformation.DoesNotExist:
        print(f"No system information found for {system_name}.")
        return None


def plot_time_series_data(sample_name_range, mode="overlay", channel_plot_logic=None):
    """
    Plots time-series data based on channel boolean logic and returns the plot as an image.

    Parameters:
    - sample_name_range: Sample name or range of sample names to filter by.
    - mode: Plotting mode ("overlay" or "panel").
    - channel_plot_logic: Dictionary with channel names as keys and booleans as values.
      Example: {"Channel 1": True, "Channel 2": False, "Channel 3": True}
    """

    # Filter SampleMetadata based on the sample_name_range
    if '-' in sample_name_range:
        start, end = sample_name_range.split('-')
        samples = SampleMetadata.objects.filter(sample_name__range=(start, end))
    else:
        samples = SampleMetadata.objects.filter(sample_name=sample_name_range)

    if not samples.exists():
        print(f"No samples found for the given range: {sample_name_range}")
        return HttpResponse("No data found for the selected sample(s).", status=404)

    # Prepare dataframes for plotting
    dataframes = []
    for sample in samples:
        time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
        df = pd.DataFrame(list(time_series.values()))
        if df.empty:
            print(f"No time-series data found for Result ID: {sample.result_id}")
            continue

        # Add metadata to the dataframe
        df["sample_name"] = sample.sample_name
        df["system_name"] = sample.system_name
        dataframes.append(df)

    if not dataframes:
        print("No time-series data found for the selected samples.")
        return HttpResponse("No time-series data found for the selected sample(s).", status=404)

    # Create the plot (make sure plt is used correctly, not HttpResponse)
    fig, ax = plt.subplots(figsize=(12, 6))  # Use a specific figure and axis

    # Relate generic channel names to the actual columns in the dataframe
    channel_mapping = {
        "Channel 1": "channel_1",
        "Channel 2": "channel_2",
        "Channel 3": "channel_3"
    }

    if mode == "overlay":
        for df in dataframes:
            sample_name = df["sample_name"].iloc[0]
            system_name = df["system_name"].iloc[0]
            system_info = query_system_information(system_name)
            if not system_info:
                print(f"Warning: No system information found for {system_name}. Skipping this sample.")
                continue

            channel_1, channel_2, channel_3 = system_info

            for generic_channel, plot in channel_plot_logic.items():
                if plot:
                    actual_column = channel_mapping.get(generic_channel)
                    if actual_column and actual_column in df.columns:
                        label = f"{sample_name} - {generic_channel}"
                        ax.plot(df["time"], df[actual_column], label=label)
                    else:
                        print(f"Warning: Column '{actual_column}' not found in the dataframe.")
        ax.legend()
        ax.set_title("Time Series Data")
        ax.set_xlabel("Time")
        ax.set_ylabel("Intensity")
        ax.grid()
    elif mode == "panel":
        fig, axs = plt.subplots(len(dataframes), 1, figsize=(12, 6 * len(dataframes)), sharex=True)
        for i, df in enumerate(dataframes):
            sample_name = df["sample_name"].iloc[0]
            system_name = df["system_name"].iloc[0]
            system_info = query_system_information(system_name)
            if not system_info:
                print(f"Warning: No system information found for {system_name}. Skipping this sample.")
                continue

            channel_1, channel_2, channel_3 = system_info
            for generic_channel, plot in channel_plot_logic.items():
                if plot:
                    actual_column = channel_mapping.get(generic_channel)
                    if actual_column and actual_column in df.columns:
                        axs[i].plot(df["time"], df[actual_column], label=generic_channel)
                    else:
                        print(f"Warning: Column '{actual_column}' not found in the dataframe.")
            axs[i].legend()
            axs[i].set_title(f"Sample: {sample_name}")
            axs[i].set_xlabel("Time")
            axs[i].set_ylabel("Intensity")
            axs[i].grid()

    # Save the plot to a BytesIO buffer
    buf = BytesIO()
    # fig.savefig(buf, format='png')
    buf.seek(0)

    # Return the image as an HTTP response
    return HttpResponse(buf.read(), content_type='image/png')


import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
from django_plotly_dash import DjangoDash

# Create Dash app
app = DjangoDash('TimeSeriesPlot')

# Layout of the app
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

    dcc.Graph(id='time_series_plot')
])


# Callback for updating the graph
@app.callback(
    Output('time_series_plot', 'figure'),
    Input('submit_button', 'n_clicks'),
    Input('sample_name_input', 'value'),
    Input('channel_selection', 'value')
)
def update_graph(n_clicks, sample_name_range, selected_channels):
    # Handle no input case
    if not sample_name_range or not selected_channels:
        return go.Figure()

    # Example query (replace with your actual database query)
    try:
        if '-' in sample_name_range:
            start, end = sample_name_range.split('-')
            samples = SampleMetadata.objects.filter(sample_name__range=(start, end))
        else:
            samples = SampleMetadata.objects.filter(sample_name=sample_name_range)

        if not samples.exists():
            return go.Figure().update_layout(title='No data found for the selected samples.')
    except Exception as e:
        return go.Figure().update_layout(title=f"Error fetching data: {str(e)}")

    # Prepare data for Plotly
    fig = go.Figure()
    for sample in samples:
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
        yaxis_title='Intensity',
        template='plotly_white'
    )
    return fig
