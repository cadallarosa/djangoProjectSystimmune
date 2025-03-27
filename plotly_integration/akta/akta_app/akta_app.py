import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
from django.db.models import F
import logging

# Replace with your actual models
from plotly_integration.models import AktaResult, AktaChromatogram, AktaRunLog, AktaFraction

logging.basicConfig(filename='akta_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = DjangoDash("AktaChromatogramApp")

def fetch_result_ids():
    """Get all available result IDs from the AktaResult table."""
    return [r["result_id"] for r in AktaResult.objects.values("result_id")]

app.layout = html.Div([
    html.Div([
        html.Label("Select Result ID:", style={"font-weight": "bold", "margin-right": "10px"}),
        dcc.Dropdown(
            id="result-id-dropdown",
            options=[{"label": rid, "value": rid} for rid in fetch_result_ids()],
            placeholder="Select a Result ID",
            style={"width": "40%"}
        )
    ], style={"margin": "10px"}),

    html.Div([
        # Left side: Plot + Info Tables
        html.Div([
            html.H4("Akta Chromatogram", style={'text-align': 'center', 'color': '#0056b3'}),
            dcc.Graph(id="chromatogram-graph"),

            # Chromatogram Info Table
            html.H4("Chromatogram Info", style={'color': '#0056b3', 'margin-top': '20px'}),
            dash_table.DataTable(
                id="chromatogram-info-table",
                columns=[],
                data=[],
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "5px",
                    "border": "1px solid #ddd",
                },
                style_header={
                    "backgroundColor": "#0056b3",
                    "fontWeight": "bold",
                    "color": "white",
                    "textAlign": "center"
                }
            ),

            # Load Volume Table
            html.H4("Load Volume", style={'color': '#0056b3', 'margin-top': '20px'}),
            dash_table.DataTable(
                id="load-volume-table",
                columns=[],  # Populated by callback
                data=[],
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "5px",
                    "border": "1px solid #ddd",
                },
                style_header={
                    "backgroundColor": "#0056b3",
                    "fontWeight": "bold",
                    "color": "white",
                    "textAlign": "center"
                }
            ),

            # Fraction Table (NEW)
            html.H4("Fraction Info", style={'color': '#0056b3', 'margin-top': '20px'}),
            dash_table.DataTable(
                id="fraction-table",
                columns=[],  # Populated by callback
                data=[],
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "5px",
                    "border": "1px solid #ddd",
                },
                style_header={
                    "backgroundColor": "#0056b3",
                    "fontWeight": "bold",
                    "color": "white",
                    "textAlign": "center"
                }
            ),
        ], style={
            "width": "70%",
            "border": "2px solid #0056b3",
            "border-radius": "5px",
            "padding": "10px",
            "background-color": "#f7f9fc"
        }),

        # Right side: Axis selection
        html.Div([
            html.H4("Plot Settings", style={'color': '#0056b3'}),

            # Left axis selection
            html.Label("Left Axis Sensors:", style={"font-weight": "bold", "margin-top": "10px"}),
            dcc.Dropdown(
                id="left-sensor-dropdown",
                options=[],  # populated dynamically
                value=[],    # user picks which sensors for the left
                multi=True,
                placeholder="Select sensors for left side"
            ),

            # Right axis selection
            html.Label("Right Axis Sensors:", style={"font-weight": "bold", "margin-top": "10px"}),
            dcc.Dropdown(
                id="right-sensor-dropdown",
                options=[],  # populated dynamically
                value=[],
                multi=True,
                placeholder="Select sensors for right side"
            )
        ], style={
            "width": "30%",
            "border": "2px solid #0056b3",
            "border-radius": "5px",
            "padding": "10px",
            "background-color": "#f7f9fc"
        }),
    ], style={"display": "flex", "flex-direction": "row", "gap": "20px", "margin": "10px"})
])

# STEP 1: Build sensor options & keep them disjoint
@app.callback(
    Output("left-sensor-dropdown", "options"),
    Output("left-sensor-dropdown", "value"),
    Output("right-sensor-dropdown", "options"),
    Output("right-sensor-dropdown", "value"),
    Input("result-id-dropdown", "value"),
    Input("left-sensor-dropdown", "value"),
    Input("right-sensor-dropdown", "value"),
    prevent_initial_call=True
)
def manage_sensor_choices(result_id, left_vals, right_vals):
    if not result_id:
        return [], [], [], []

    qs = AktaChromatogram.objects.filter(result_id=result_id).values()
    df = pd.DataFrame(qs)
    if df.empty:
        return [], [], [], []

    # Available sensors
    all_sensors = [c for c in df.columns if c not in ["id", "result_id", "ml"]]

    # Convert current picks to sets
    left_vals = set(left_vals or [])
    right_vals = set(right_vals or [])

    # Set default to 'uv1' if available and not already selected
    default_sensor = "uv_1_280"
    if default_sensor in all_sensors:
        if not left_vals:  # If left sensors are empty, default to 'uv1'
            left_vals.add(default_sensor)
        elif default_sensor in right_vals:  # Ensure 'uv1' isn't in both
            right_vals.remove(default_sensor)

    # Ensure disjoint
    overlap = left_vals & right_vals
    if overlap:
        # Remove overlap from right side, left side wins
        right_vals = right_vals - overlap

    # Filter out any sensors that no longer exist
    left_vals = left_vals.intersection(all_sensors)
    right_vals = right_vals.intersection(all_sensors)

    left_options = [{"label": s, "value": s} for s in all_sensors if s not in right_vals]
    right_options = [{"label": s, "value": s} for s in all_sensors if s not in left_vals]



    return left_options, sorted(left_vals), right_options, sorted(right_vals)


# STEP 2: Chromatogram Info Table
@app.callback(
    [Output("chromatogram-info-table", "columns"),
     Output("chromatogram-info-table", "data")],
    Input("result-id-dropdown", "value"),
    prevent_initial_call=True
)
def update_chromatogram_info_table(result_id):
    if not result_id:
        return [], []
    row = AktaResult.objects.filter(result_id=result_id).values().first()
    if not row:
        return [], []
    df = pd.DataFrame([row])
    columns = [{"name": c, "id": c} for c in df.columns]
    data = df.to_dict("records")
    return columns, data


#Load Volume Table
import pandas as pd

# STEP 2b: Load Volume Table
@app.callback(
    [Output("load-volume-table", "columns"),
     Output("load-volume-table", "data")],
    [Input("result-id-dropdown", "value")],
    prevent_initial_call=True
)
def update_load_volume_table(result_id):
    """
    1) Query AktaRunLog for the chosen result_id, ordered by ml.
    2) Find first 'Block Direct sample injection' => injection_ml
    3) Find first 'End_Block' after that => end_block_ml
    4) load_volume = end_block_ml - injection_ml
    5) Display in DataTable
    """
    if not result_id:
        return [], []

    # Fetch relevant data
    run_logs = (
        AktaRunLog.objects
        .filter(result_id=result_id)
        .order_by("ml")  # ascending order
        .values("ml", "log_text")
    )

    if not run_logs.exists():
        return [], []

    # Convert QuerySet to DataFrame
    df = pd.DataFrame(list(run_logs))

    if df.empty:
        return [], []

    injection_ml = None
    end_block_ml = None
    load_volume = 0.0
    found_injection = False

    # Iterate through DataFrame rows
    for _, row in df.iterrows():
        txt = (row["log_text"] or "").lower()
        ml_val = row["ml"] or 0.0

        # If we see "Block Start frac (Sample Appl) (Issued) (Processing) (Completed)"
        if "block start frac (sample appl) (issued) (processing) (completed)" in txt:
            found_injection = True
            injection_ml = ml_val

        # Once injection is found, find the first "end_block"
        elif found_injection and "end_block" in txt:
            end_block_ml = ml_val
            load_volume = end_block_ml - (injection_ml or 0)
            break

    # Store results in a DataFrame
    result_df = pd.DataFrame([{
        "Sample Application Start": injection_ml if injection_ml is not None else "",
        "Sample Application End": end_block_ml if end_block_ml is not None else "",
        "Load Volume": load_volume
    }])

    # Convert DataFrame to Dash Table format
    table_columns = [{"name": col, "id": col} for col in result_df.columns]
    table_data = result_df.to_dict("records")

    return table_columns, table_data



# STEP 2c: Fraction Table
@app.callback(
    [Output("fraction-table", "columns"),
     Output("fraction-table", "data")],
    [Input("result-id-dropdown", "value")],
    prevent_initial_call=True
)
def update_fraction_table(result_id):
    """
    1) Query AktaFraction for the chosen result_id, sorted by ml ascending (including waste).
    2) Convert to DataFrame.
    3) Reshape DataFrame to include fraction start and end.
    4) Drop waste rows after setting up fractionation start and end.
    5) Return table with fraction info.
    """
    if not result_id:
        return [], []

    # 1) Fetch ALL fraction rows for that result_id, sorted by ml ascending
    fraction_qs = (AktaFraction.objects
                   .filter(result_id=result_id)
                   .order_by("ml"))

    if not fraction_qs.exists():
        return [], []

    # 2) Convert to DataFrame
    df = pd.DataFrame(list(fraction_qs.values("ml", "fraction")))
    print(df)
    df = df.drop_duplicates(subset=['ml']).reset_index(drop=True)

    # 3) Rename 'ml' to 'fraction_start' and add 'fraction_end'
    df.rename(columns={"ml": "fraction_start"}, inplace=True)
    df["fraction_end"] = df["fraction_start"].shift(-1)

    # 4) Compute fraction volume
    df["fraction_volume"] = df["fraction_end"] - df["fraction_start"]

    # 5) Drop waste rows
    df = df[~df["fraction"].str.lower().str.contains("waste", na=False)].copy()

    if df.empty:
        return [], []

    # Reorder columns for clarity
    df = df[["fraction", "fraction_start", "fraction_end", "fraction_volume"]]

    # Build columns/data for dash table
    columns = [{"name": col.replace("_", " ").title(), "id": col} for col in df.columns]
    data = df.to_dict("records")

    return columns, data




# STEP 3: Plot - same domain, different y-axes, but offset so axes don't overlap
@app.callback(
    Output("chromatogram-graph", "figure"),
    [
        Input("result-id-dropdown", "value"),
        Input("left-sensor-dropdown", "value"),
        Input("right-sensor-dropdown", "value")
    ],
    prevent_initial_call=True
)
def update_chromatogram_plot(result_id, left_sensors, right_sensors):
    fig = go.Figure()
    if not result_id:
        return fig

    qs = AktaChromatogram.objects.filter(result_id=result_id).values()
    df = pd.DataFrame(qs)
    # Sort by ml to avoid wrap-around lines
    df = df.sort_values(by='ml', ascending=True)

    if df.empty:
        return fig

    left_sensors = left_sensors or []
    right_sensors = right_sensors or []

    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ]

    axis_counter = 1  # keep track of how many axes we've created so far

    # 1) Left side
    for i, sensor in enumerate(left_sensors):
        if sensor not in df.columns:
            continue

        axis_id = "" if axis_counter == 1 else str(axis_counter)
        yaxis_name = f"yaxis{axis_id}"
        yaxis_id   = f"y{axis_id}"

        y_data = df[sensor]
        y_min, y_max = y_data.min(), y_data.max()
        if y_min == y_max:
            y_min -= 1
            y_max += 1

        color = default_colors[(axis_counter - 1) % len(default_colors)]

        fig.add_trace(go.Scatter(
            x=df["ml"],
            y=y_data,
            name=sensor,
            mode="lines",
            yaxis=yaxis_id,
            line=dict(color=color),
            connectgaps=False
        ))

        position_left = 0.0 + 0.05 * i
        if position_left > 0.4:
            position_left = 0.4

        if axis_counter == 1:
            # first axis in the entire figure
            fig.update_layout(**{
                yaxis_name: dict(
                    title=dict(text=sensor, font=dict(color=color)),
                    side="left",
                    range=[y_min, y_max]
                )
            })
        else:
            fig.update_layout(**{
                yaxis_name: dict(
                    title=dict(text=sensor, font=dict(color=color)),
                    side="left",
                    range=[y_min, y_max],
                    overlaying="y",
                    anchor="free",
                    position=position_left
                )
            })
        axis_counter += 1

    # 2) Right side
    for j, sensor in enumerate(right_sensors):
        if sensor not in df.columns:
            continue

        axis_id = "" if axis_counter == 1 else str(axis_counter)
        yaxis_name = f"yaxis{axis_id}"
        yaxis_id   = f"y{axis_id}"

        y_data = df[sensor]
        y_min, y_max = y_data.min(), y_data.max()
        if y_min == y_max:
            y_min -= 1
            y_max += 1

        color = default_colors[(axis_counter - 1) % len(default_colors)]

        fig.add_trace(go.Scatter(
            x=df["ml"],
            y=y_data,
            name=sensor,
            mode="lines",
            yaxis=yaxis_id,
            line=dict(color=color),
            connectgaps=False
        ))

        position_right = 1.0 - 0.05 * j
        if position_right < 0.6:
            position_right = 0.6

        if axis_counter == 1:
            fig.update_layout(**{
                yaxis_name: dict(
                    title=dict(text=sensor, font=dict(color=color)),
                    side="right",
                    range=[y_min, y_max]
                )
            })
        else:
            fig.update_layout(**{
                yaxis_name: dict(
                    title=dict(text=sensor, font=dict(color=color)),
                    side="right",
                    range=[y_min, y_max],
                    overlaying="y",
                    anchor="free",
                    position=position_right
                )
            })

        axis_counter += 1

    fig.update_layout(
        title=f"Akta Chromatogram: {result_id}",
        xaxis=dict(title="ml"),
        template="plotly_white"
    )
    return fig
