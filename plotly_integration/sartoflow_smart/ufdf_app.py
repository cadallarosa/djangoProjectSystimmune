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
    "AG2100_Value", "AG2100_Setpoint", "AG2100_Mode", "AG2100_Output",
    "DPRESS_Value", "DPRESS_Output", "DPRESS_Mode", "DPRESS_Setpoint",
    "F_PERM_Value",
    "P2500_Setpoint", "P2500_Value", "P2500_Output", "P2500_Mode",
    "P3000_Setpoint", "P3000_Mode", "P3000_Output", "P3000_Value", "P3000_T",
    "PIR2600", "PIR2700",
    "PIRC2500_Output", "PIRC2500_Value", "PIRC2500_Setpoint", "PIRC2500_Mode",
    "QIR2000", "QIR2100",
    "TIR2100", "TMP",
    "WIR2700",
    "WIRC2100_Output", "WIRC2100_Setpoint", "WIRC2100_Mode"
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
                    options=[{"label": col, "value": col} for col in selectable_columns],
                    value=["AG2100_Value"],  # Default selection
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

    for column in selected_columns:
        if column in df.columns:
            fig.add_trace(go.Scatter(x=df["process_time"], y=df[column], mode="lines", name=column))
        else:
            print(f"Warning: Column {column} not found in DataFrame")

    fig.update_layout(
        title=f"Batch {selected_batch} - Time Series Data",
        xaxis_title="Process Time",
        yaxis_title="Value",
        template="plotly_white"
    )

    return fig
