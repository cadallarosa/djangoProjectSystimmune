import pandas as pd
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output
from plotly_integration.models import SartoflowTimeSeriesData

# Create Dash App
app = DjangoDash("UFDFApp")

# Query the database for unique batch IDs
batch_ids = SartoflowTimeSeriesData.objects.values_list("batch_id", flat=True).distinct()

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
]

# Dash Layout
app.layout = html.Div(
    style={"display": "flex", "flexDirection": "row", "gap": "20px", "padding": "20px"},
    children=[
        # Left Sidebar - Batch Selection & Checkboxes
        html.Div(
            style={"width": "25%", "border": "1px solid #ccc", "padding": "10px", "borderRadius": "5px"},
            children=[
                html.H3("Select Batch ID"),
                dcc.Dropdown(
                    id="batch-dropdown",
                    options=[{"label": batch, "value": batch} for batch in batch_ids],
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
    ],
)


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

    # Debugging: Print available columns
    print("Available columns in DataFrame:", df.columns.tolist())

    # Convert selected columns to lowercase to match database column names
    selected_columns = [col.lower() for col in selected_columns]

    fig = go.Figure()

    # Define axis mappings dynamically
    axis_map = {}
    y_axis_count = 1

    for i, column in enumerate(selected_columns):
        if column in df.columns:
            y_axis_name = "y" if y_axis_count == 1 else f"y{y_axis_count}"
            axis_map[column] = y_axis_name

            fig.add_trace(go.Scatter(
                x=df["process_time"],
                y=df[column],
                mode="lines",
                name=column,
                yaxis=y_axis_name
            ))

            y_axis_count += 1
        else:
            print(f"Warning: Column {column} not found in DataFrame")

    # Layout with multiple y-axes
    layout = {
        "title": f"Batch {selected_batch} - Time Series Data",
        "xaxis": {"title": "Process Time"},
        "yaxis": {
            "title": selected_columns[0] if selected_columns else "Value",
            "side": "left",
            "showgrid": True
        }
    }

    # Dynamically add secondary axes
    for i, column in enumerate(selected_columns[1:], start=2):
        layout[f"yaxis{i}"] = {
            "title": column,
            "overlaying": "y",  # Overlay on primary y-axis
            "side": "right" if i % 2 == 0 else "left",  # Alternate sides
            "showgrid": False
        }

    fig.update_layout(layout, template="plotly_white")

    return fig
