import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from django_plotly_dash import DjangoDash

# Create Dash app
app = DjangoDash('TimeSeriesPlot')

# Layout of the app
app.layout = html.Div([
    html.H1('Plotly Dash Integration'),
    dcc.Input(id='sample_name_input', type='text', placeholder='Enter sample name or range', style={'width': '300px'}),
    html.Button('Submit', id='submit_button', n_clicks=0),
    dcc.Checklist(
        id='channel_selection',
        options=[
            {'label': 'Channel 1', 'value': 'channel_1'},
            {'label': 'Channel 2', 'value': 'channel_2'},
            {'label': 'Channel 3', 'value': 'channel_3'},
        ],
        value=['channel_1', 'channel_2', 'channel_3'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='time_series_plot')
])


# Callback to update the plot based on input
@app.callback(
    Output('time_series_plot', 'figure'),
    [Input('submit_button', 'n_clicks'),
     Input('sample_name_input', 'value'),
     Input('channel_selection', 'value')]
)
def update_graph(n_clicks, sample_name_range, selected_channels):
    # Example data; replace this with your actual data fetching logic
    data = {
        'time': [1, 2, 3, 4, 5],
        'channel_1': [10, 12, 13, 15, 16],
        'channel_2': [5, 7, 9, 10, 12],
        'channel_3': [1, 3, 4, 6, 8]
    }
    df = pd.DataFrame(data)

    fig = go.Figure()
    for channel in selected_channels:
        if channel in df.columns:
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df[channel],
                mode='lines',
                name=channel
            ))

    fig.update_layout(
        title='Time Series Data',
        xaxis_title='Time',
        yaxis_title='Intensity'
    )

    return fig
