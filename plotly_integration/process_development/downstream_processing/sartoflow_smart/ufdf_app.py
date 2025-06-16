import dash
import pandas as pd
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output, State
from plotly_integration.models import SartoflowTimeSeriesData

# Create Dash App
app = DjangoDash("UFDFApp")

# # Query the database for unique batch IDs
# batch_ids = SartoflowTimeSeriesData.objects.values_list("batch_id", flat=True).distinct()

# Define selectable columns (except BatchId and ProcessTime)
selectable_columns = [
    {"label": "Agitator Speed (AG_2100)", "value": "AG2100_Value"},
    {"label": "Differential Pressure (DPRESS)", "value": "DPRESS_Value"},
    {"label": "Filtrate Flow Rate (F_PERM)", "value": "F_PERM_Value"},
    {"label": "Feed Pump Output (P2500)", "value": "P2500_Output"},
    {"label": "Fill Pump Output (P3000 Output)", "value": "P3000_Output"},
    {"label": "Fill Pump Totalizer (P3000_T)", "value": "P3000_T"},
    {"label": "Retentate Pressure (PIR2600)", "value": "PIR2600"},
    {"label": "Permeate Pressure (PIR2700)", "value": "PIR2700"},
    {"label": "Feed Pressure (PIRC2500)", "value": "PIRC2500_Value"},
    {"label": "Process Temperature (TIR2100)", "value": "TIR2100"},
    {"label": "TMP (bar)", "value": "TMP"},
    {"label": "Permeate Weight (WIR2700)", "value": "WIR2700"},
    {"label": "Retain Vessel Weight (WIRC2100)", "value": "WIRC2100_SETPOINT"},
    {"label": "Feed Flow Rate (mL/min)", "value": "feed_flow_rate"},
    {"label": "Permeate Flow Rate (mL/min)", "value": "permeate_flow_rate"},
    {"label": "Retentate Flow Rate (mL/min)", "value": "retentate_flow_rate"},
    {"label": "Flux/Feed Rate", "value": "flux_decay"},
    {"label": "Flux (L/m²/hr)", "value": "flux"},

]

# Create a lookup for value → label
label_map = {item["value"].lower(): item["label"] for item in selectable_columns}

# Dash Layout
app.layout = html.Div(
    style={"display": "flex", "flexDirection": "row", "gap": "20px", "padding": "20px"},
    children=[
        dcc.Store(id='has-selected-batch', data=False),
        # Left Sidebar - Batch Selection & Checkboxes
        html.Div(
            style={"width": "25%", "border": "1px solid #ccc", "padding": "10px", "borderRadius": "5px"},
            children=[
                html.H3("Select Batch ID"),
                dcc.Dropdown(
                    id="batch-dropdown",
                    options=[],
                    placeholder="Select a batch...",
                    style={"marginBottom": "10px"}
                ),
                html.H3("Select Data to Plot"),
                dcc.Checklist(
                    id="data-selection",
                    options=selectable_columns,
                    value=["TMP"],  # Default selection
                    style={"display": "flex", "flexDirection": "column"}
                ),
            ],
        ),
        # Graph Area
        html.Div(
            style={"width": "75%", "border": "1px solid #ccc", "padding": "10px", "borderRadius": "5px"},
            children=[
                html.H3("Time Series Data"),
                dcc.Graph(id="time-series-graph"),
            ],
        ),
        dcc.Interval(
            id='refresh-interval',
            interval=10 * 1000,  # Every 10 seconds
            n_intervals=0
        ),
    ],
)


@app.callback(
    Output("batch-dropdown", "options"),
    Input("refresh-interval", "n_intervals")
)
def update_batch_dropdown(n):
    batch_ids = SartoflowTimeSeriesData.objects.values_list("batch_id", flat=True).distinct()
    return [{"label": batch, "value": batch} for batch in batch_ids if batch]


@app.callback(
    Output("batch-dropdown", "value"),
    Output("has-selected-batch", "data"),
    Input("batch-dropdown", "options"),
    State("has-selected-batch", "data"),
    prevent_initial_call=True
)
def set_initial_batch(options, has_selected):
    if not has_selected and options:
        return options[-1]["value"], True  # Only auto-select once
    return dash.no_update, has_selected


@app.callback(
    Output("time-series-graph", "figure"),
    Input("batch-dropdown", "value"),
    Input("data-selection", "value")
)
def update_graph(selected_batch, selected_columns):
    if not selected_batch:
        return go.Figure()

    # Query database for selected batch
    query_set = SartoflowTimeSeriesData.objects.filter(batch_id=selected_batch).values()
    df = pd.DataFrame.from_records(query_set)

    if df.empty:
        return go.Figure()

    df = df.sort_values(by="process_time")
    # df = df[~df.duplicated(subset=['wir2700'], keep=False)].reset_index(drop=True)

    # Calculated columns
    df['feed_flow_rate'] = df['p2500_output'] * 16.67
    df['diff_wir2700'] = df['wir2700'].diff() / 1000
    df['diff_time'] = df['process_time'].diff()
    df['permeate_flow_rate'] = (df['diff_wir2700'] / df['diff_time']) * 16.667
    df['permeate_flow_rate'] = df['permeate_flow_rate'].rolling(window=10).mean()
    df['retentate_flow_rate'] = df['feed_flow_rate'] - df['permeate_flow_rate']
    df['flux_decay'] = df['permeate_flow_rate'] / df['feed_flow_rate']
    df['flux'] = df['permeate_flow_rate'] / 0.02

    # Convert selected columns to lowercase
    selected_columns = [col.lower() for col in selected_columns]

    fig = go.Figure()
    axis_map = {}
    y_axis_count = 1

    for column in selected_columns:
        if column in df.columns:
            y_axis_name = "y" if y_axis_count == 1 else f"y{y_axis_count}"
            axis_map[column] = y_axis_name

            fig.add_trace(go.Scatter(
                x=df["process_time"],
                y=df[column],
                mode="lines",
                name=label_map.get(column, column),
                yaxis=y_axis_name
            ))

            y_axis_count += 1
        else:
            print(f"⚠️ Warning: Column '{column}' not found in DataFrame.")

    # Layout with multiple Y-axes and 0 min range
    layout = {
        "title": f"Batch {selected_batch} - Time Series Data",
        "xaxis": {"title": "Process Time (hrs)"},
    }

    for i, column in enumerate(selected_columns, start=1):
        axis_key = "yaxis" if i == 1 else f"yaxis{i}"
        axis_name = "y" if i == 1 else f"y{i}"

        axis_config = {
            "title": label_map.get(column, column),
            "overlaying": "y" if i > 1 else None,
            "side": "right" if i % 2 == 0 else "left",
            "showgrid": i == 1,
        }

        if column == "flux_decay":
            axis_config["range"] = [0, 1]  # Force fixed scale for flux/feed
        else:
            axis_config["rangemode"] = "tozero"

        layout[axis_key] = axis_config

    # Dynamically add extra y-axes
    for i, column in enumerate(selected_columns[1:], start=2):
        layout[f"yaxis{i}"] = {
            "title": label_map.get(column, column),
            "overlaying": "y",
            "side": "right" if i % 2 == 0 else "left",
            "showgrid": False,
            "rangemode": "tozero"  # Also enforce 0 min
        }

    fig.update_layout(layout, template="plotly_white")

    return fig
