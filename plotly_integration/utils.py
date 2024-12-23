import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from django_plotly_dash import DjangoDash

# Create Dash app
app = DjangoDash('TimeSeriesPlot')

# Layout of the app
app.layout = html.Div([
    dcc.Input(
        id='sample_name_input',
        type='text',
        placeholder='Enter sample name or range (e.g., S1-S5)',
        style={'width': '300px'}
    ),
    html.Button('Submit', id='submit_button', n_clicks=0),
    dcc.Checklist(
        id='channel_selection',
        options=[
            {'label': 'Channel 1', 'value': 'channel_1'},
            {'label': 'Channel 2', 'value': 'channel_2'},
            {'label': 'Channel 3', 'value': 'channel_3'},
        ],
        value=['channel_1', 'channel_2', 'channel_3'],
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
    if not sample_name_range or not selected_channels:
        return go.Figure()

    # Here we would fetch data and plot it, for now we'll simulate with dummy data
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[1, 2, 3, 4],
        y=[10, 11, 12, 13],
        mode='lines',
        name='Example Data'
    ))

    fig.update_layout(
        title='Time Series Data',
        xaxis_title='Time',
        yaxis_title='Intensity',
        template='plotly_white'
    )
    return fig
