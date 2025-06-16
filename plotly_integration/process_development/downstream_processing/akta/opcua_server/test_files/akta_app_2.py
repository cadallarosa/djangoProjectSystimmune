import numpy as np
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output, dash_table, State
import pandas as pd
from django.db.models import F
import logging
from plotly_integration.models import AktaResult, AktaChromatogram, AktaRunLog, AktaFraction

AXIS_LABELS = {
    "uv_1_280": "UV 280 nm (mAU)",
    "uv_2_0": "UV 2.0 (mAU)",
    "uv_3_0": "UV 3.0 (mAU)",
    "cond": "Conductivity (mS/cm)",
    "conc_b": "Concentration B (%)",
    "pH": "pH",
    "system_flow": "System Flow (mL/min)",
    "system_linear_flow": "System Linear Flow (cm/h)",
    "system_pressure": "System Pressure (bar)",
    "cond_temp": "Conductivity Temp (°C)",
    "sample_flow": "Sample Flow (mL/min)",
    "sample_linear_flow": "Sample Linear Flow (cm/h)",
    "sample_pressure": "Sample Pressure (bar)",
    "preC_pressure": "Pre-column Pressure (bar)",
    "deltaC_pressure": "Delta Column Pressure (bar)",
    "postC_pressure": "Post-column Pressure (bar)"
}

TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "2px 4px",
    "fontSize": "11px",
    "border": "1px solid #ddd",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#0056b3",
    "fontWeight": "bold",
    "color": "white",
    "textAlign": "center",
    "fontSize": "11px",
    "padding": "2px 4px"
}

TABLE_STYLE_TABLE = {
    "overflowX": "auto",
    "overflowY": "auto",
    "maxHeight": "250px"
}

logging.basicConfig(filename='akta_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = DjangoDash("AktaChromatogramApp")

app.layout = html.Div([
    html.Div([  # Main content container
        dcc.Tabs(id="main-tabs", value="tab-1", children=[

            # 🔹 Tab 1: Sample Analysis
            dcc.Tab(label="Select Result", value="tab-1", children=[
                html.Div([
                    html.Label("Select Result ID:", style={"font-weight": "bold", "margin-right": "10px"}),
                    dash_table.DataTable(
                        id="result-table",
                        columns=[
                            {"name": "Result ID", "id": "result_id"},
                            {"name": "Result Name", "id": "result_name"},
                            {"name": "Date Acquired", "id": "date"},
                            {"name": "Method", "id": "method"},
                            {"name": "User", "id": "user"},
                            {"name": "System Name", "id": "system"},
                            {"name": "Result Path", "id": "result_path"},
                        ],
                        data=[],
                        row_selectable="single",
                        style_table={
                            "overflowX": "auto",
                            "overflowY": "auto",
                            "height": "80vh",  # 🔥 make it take most of the page height
                            "maxHeight": "80vh",
                        },
                        style_cell={
                            "textAlign": "left",
                            "padding": "3px",
                            "fontSize": "12px",
                            "height": "25px",
                        },
                        style_header={
                            "backgroundColor": "#0056b3",
                            "color": "white",
                            "fontWeight": "bold",
                            "fontSize": "12px",
                            "padding": "4px"
                        },
                        filter_action="native",
                        sort_action="native",
                        page_size=20
                    )
                ], style={
                    "width": "100%",
                    "height": "100vh",  # 🔥 full page height
                    "margin": 0,
                    "padding": "10px",
                    "boxSizing": "border-box"
                })]),

            dcc.Tab(label="Chromatogram Analysis", value="tab-2", children=[
                html.Div([
                    dcc.Store(id="selected-result-id", data=None),
                    dcc.Store(id="load-volume-store", data=None),
                    dcc.Store(id="titer-store", data={"titer": 0.0}),
                    dcc.Store(id="x-axis-offset", data=None),

                    dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),
                    # Left side: Plot + Info Tables
                    html.Div([
                        dcc.Graph(id="chromatogram-graph"),

                        # # Chromatogram Info Table
                        # html.H4("Chromatogram Info", style={'color': '#0056b3', 'margin-top': '20px'}),
                        # dash_table.DataTable(
                        #     id="chromatogram-info-table",
                        #     columns=[],
                        #     data=[],
                        #     style_table=TABLE_STYLE_TABLE,
                        #     style_cell=TABLE_STYLE_CELL,
                        #     style_header=TABLE_STYLE_HEADER
                        # ),

                        # Load Volume Table
                        html.H4("Load Volume", style={'color': '#0056b3', 'margin-top': '0px'}),
                        dash_table.DataTable(
                            id="load-volume-table",
                            columns=[],  # Populated by callback
                            data=[],
                            style_table=TABLE_STYLE_TABLE,
                            style_cell=TABLE_STYLE_CELL,
                            style_header=TABLE_STYLE_HEADER
                        ),

                        # Fraction Table (NEW)
                        html.H4("Fractions", style={'color': '#0056b3', 'margin-top': '5px'}),
                        dash_table.DataTable(
                            id="fraction-table",
                            columns=[],  # Populated by callback
                            data=[],
                            fixed_rows={'headers': True},
                            style_table=TABLE_STYLE_TABLE,
                            style_cell=TABLE_STYLE_CELL,
                            style_header=TABLE_STYLE_HEADER
                        ),
                    ], style={
                        "width": "85%",
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
                            value=[],  # user picks which sensors for the left
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
                        ),
                        html.Label("Options:", style={"font-weight": "bold", "margin-top": "10px"}),
                        dcc.Checklist(
                            id="plot-options-checklist",
                            options=[
                                {"label": "Zero x-axis at Sample Application", "value": "zero_ml"}
                            ],
                            value=["zero_ml"],
                            style={"margin-bottom": "10px"}
                        ),
                        html.Label("E1%", style={"font-weight": "bold", "margin-top": "10px"}),
                        dcc.Input(
                            id="extinction-coefficient",  # keep the same ID
                            type="number",
                            value=16.19,
                            step=0.01,
                            style={"width": "100%", "margin-bottom": "10px"}
                        ),
                    ], style={
                        "width": "15%",
                        "border": "2px solid #0056b3",
                        "border-radius": "5px",
                        "padding": "10px",
                        "background-color": "#f7f9fc"
                    }),
                ], style={"display": "flex", "flex-direction": "row", "gap": "20px", "margin": "10px"})])
        ])
    ])
])


@app.callback(
    Output("result-table", "data"),
    Input("load-once", "n_intervals")
)
def load_result_table(_):
    results = AktaResult.objects.all().order_by("-date")[:500]
    table_data = []

    for r in results:
        table_data.append({
            "result_id": r.result_id,
            "result_name": r.report_name,
            'user': r.user,
            # "system": getattr(r, "system", ""),
            "method": getattr(r, "method", ""),
            "date": r.date.strftime("%Y-%m-%d") if r.date else "",
            "result_path": getattr(r, "result_path", ""),
        })
    return table_data


@app.callback(
    Output("result-table", "selected_rows"),
    Input("result-table", "data"),
    prevent_initial_call=True
)
def auto_select_first_row(data):
    # Only trigger on first table load
    if data and len(data) > 0:
        return [0]
    return []


@app.callback(
    Output("selected-result-id", "data"),
    Input("result-table", "selected_rows"),
    State("result-table", "data")
)
def select_result_id(selected_rows, table_data):
    if selected_rows:
        return table_data[selected_rows[0]]["result_id"]
    return None


# STEP 1: Build sensor options & keep them disjoint
@app.callback(
    Output("left-sensor-dropdown", "options"),
    Output("left-sensor-dropdown", "value"),
    Output("right-sensor-dropdown", "options"),
    Output("right-sensor-dropdown", "value"),
    Input("selected-result-id", "data"),
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

    left_options = [{"label": AXIS_LABELS.get(s, s), "value": s} for s in all_sensors if s not in right_vals]
    right_options = [{"label": AXIS_LABELS.get(s, s), "value": s} for s in all_sensors if s not in left_vals]

    return left_options, sorted(left_vals), right_options, sorted(right_vals)


# # STEP 2: Chromatogram Info Table
# @app.callback(
#     [Output("chromatogram-info-table", "columns"),
#      Output("chromatogram-info-table", "data")],
#     Input("selected-result-id", "data"),
#     prevent_initial_call=True
# )
# def update_chromatogram_info_table(result_id):
#     if not result_id:
#         return [], []
#     row = AktaResult.objects.filter(result_id=result_id).values().first()
#     if not row:
#         return [], []
#     df = pd.DataFrame([row])
#     columns = [{"name": c, "id": c} for c in df.columns]
#     data = df.to_dict("records")
#     return columns, data


@app.callback(
    Output("titer-store", "data"),
    Input("load-volume-table", "data"),
    prevent_initial_call=True
)
def update_titer_from_table(table_data):
    if table_data and isinstance(table_data, list):
        titer_val = table_data[0].get("titer", 0.0)
        return {"titer": titer_val}
    return {"titer": 0.0}


@app.callback(
    [Output("load-volume-table", "columns"),
     Output("load-volume-table", "data")],
    [Input("load-volume-store", "data"),
     Input("titer-store", "data"),
     Input("x-axis-offset", "data")],
    prevent_initial_call=True
)
def update_load_volume_table(load_data, titer_data, x_offset_ml):
    if not load_data:
        return [], []

    titer = titer_data.get("titer", 1.0)
    load_volume = load_data["load_volume"]
    load_mass = round(titer * load_volume, 2)

    result_df = pd.DataFrame([{
        "start_ml": round(load_data["start_ml"] - x_offset_ml, 2),
        "end_ml": round(load_data["end_ml"] - x_offset_ml, 2),
        "load_volume": round(load_volume, 2),
        "titer": titer,
        "load_mass": load_mass
    }])

    table_columns = [
        {"name": "Sample Application Start", "id": "start_ml", "type": "numeric"},
        {"name": "Sample Application End", "id": "end_ml", "type": "numeric"},
        {"name": "Load Volume", "id": "load_volume", "type": "numeric"},
        {"name": "Titer (mg/mL)", "id": "titer", "type": "numeric", "editable": True},
        {"name": "Load Mass (mg)", "id": "load_mass", "type": "numeric"},
    ]

    return table_columns, result_df.to_dict("records")


# STEP 2c: Fraction Table
@app.callback(
    [Output("fraction-table", "columns"),
     Output("fraction-table", "data")],
    [Input("selected-result-id", "data"),
     Input("x-axis-offset", "data")],
    [State("extinction-coefficient", "value")],
    prevent_initial_call=True
)
def update_fraction_table(result_id, x_axis_offset, extinction_coeff):
    if not result_id:
        return [], []

    # 1. Fetch chromatogram and fraction data
    chrom_df = pd.DataFrame(
        AktaChromatogram.objects.filter(result_id=result_id).values("ml", "uv_1_280", "date_time")
    )
    chrom_df["date_time"] = pd.to_datetime(chrom_df["date_time"])
    chrom_df = chrom_df.sort_values("date_time")

    fraction_qs = AktaFraction.objects.filter(result_id=result_id).order_by("date_time")
    if not fraction_qs.exists():
        return [], []

    frac_df = pd.DataFrame(list(fraction_qs.values("date_time", "fraction")))
    frac_df["date_time"] = pd.to_datetime(frac_df["date_time"])
    frac_df = frac_df.drop_duplicates(subset=["fraction"]).reset_index(drop=True)

    # 2. Lookup corresponding start_ml
    start_mls = []
    for t in frac_df["date_time"]:
        idx = (chrom_df["date_time"] - t).abs().idxmin()
        start_mls.append(chrom_df.loc[idx, "ml"] if pd.notnull(idx) else None)

    frac_df["start_ml"] = start_mls
    frac_df["end_ml"] = frac_df["start_ml"].shift(-1)
    frac_df["volume_ml"] = frac_df["end_ml"] - frac_df["start_ml"]

    # Drop waste rows
    frac_df = frac_df[~frac_df["fraction"].str.lower().str.contains("waste", na=False)].copy()

    # 3. Calculate AUC, mass, and concentration
    auc_list = []
    mass_list = []
    conc_list = []

    e1_percent = extinction_coeff
    path_length = 0.2  # user-set or fixed for now
    ext_coeff = e1_percent * path_length * 100  # convert to mAU·mL/mg

    chrom_df = chrom_df.sort_values("ml")

    for _, row in frac_df.iterrows():
        start = row["start_ml"]
        end = row["end_ml"]
        vol = row["volume_ml"]

        subset = chrom_df[(chrom_df["ml"] >= start) & (chrom_df["ml"] <= end)]

        if not subset.empty:
            auc = np.trapz(subset["uv_1_280"].fillna(0), subset["ml"])
            mass = auc / ext_coeff if ext_coeff else 0
            conc = mass / vol if vol > 0 else 0
        else:
            auc = mass = conc = 0

        auc_list.append(round(auc, 2))
        mass_list.append(round(mass, 2))
        conc_list.append(round(conc, 2))

    frac_df["auc"] = auc_list
    frac_df["mass"] = mass_list
    frac_df["concentration"] = conc_list

    # 4. Build table
    display_df = frac_df[[
        "fraction", "start_ml", "end_ml", "volume_ml", "auc", "mass", "concentration"
    ]].dropna()

    display_df['start_ml'] = display_df['start_ml'] - x_axis_offset
    display_df['end_ml'] = display_df['end_ml'] - x_axis_offset

    display_df = display_df.round(2)
    display_df = display_df.rename(columns={
        "fraction": "Fraction",
        "start_ml": "Start (mL)",
        "end_ml": "End (mL)",
        "volume_ml": "Volume (mL)",
        "auc": "AUC (mAU·mL)",
        "mass": "Mass (mg)",
        "concentration": "Conc. (mg/mL)"
    })

    columns = [{"name": col, "id": col} for col in display_df.columns]
    data = display_df.to_dict("records")

    return columns, data


def extract_phases(result_id):
    logs = AktaRunLog.objects.filter(result_id=result_id).order_by("date_time").values("date_time", "ml", "log_text")
    df = pd.DataFrame(logs).dropna(subset=["log_text"])

    phases = []
    phase_start = None

    for _, row in df.iterrows():
        log = row["log_text"]

        if log.startswith("Phase ") and "(Issued)" in log and "(Processing)" in log:
            # Start of a new phase
            phase_name = log.replace("Phase ", "").split(" (")[0]

            if phase_name == "Method Settings":
                phase_start = None  # Skip this phase entirely
                continue

            phase_start = {
                "label": phase_name,
                "start_time": row["date_time"],
                "start_ml": row["ml"]
            }

        elif "End Phase (Issued) (Processing) (Completed)" in log and phase_start:
            # End of the current phase
            phase_start.update({
                "end_time": row["date_time"],
                "end_ml": row["ml"]
            })
            phases.append(phase_start)
            phase_start = None

    # Handle final phase with fallback to End_Block
    if phase_start:
        end_blocks = df[df["log_text"].str.contains("End_Block \(Issued\) \(Processing\) \(Completed\)", na=False)]
        if not end_blocks.empty:
            last = end_blocks.iloc[-1]
            phase_start.update({
                "end_time": last["date_time"],
                "end_ml": last["ml"]
            })
            phases.append(phase_start)

    return pd.DataFrame(phases)


def fill_phase_mLs(phases_df, chrom_df):
    # Ensure datetime is parsed and sorted
    chrom_df = chrom_df.sort_values("date_time").copy()
    chrom_df["date_time"] = pd.to_datetime(chrom_df["date_time"])

    # Ensure phases_df is datetime typed too
    phases_df["start_time"] = pd.to_datetime(phases_df["start_time"])
    phases_df["end_time"] = pd.to_datetime(phases_df["end_time"])

    # Find closest ml to start_time and end_time
    start_mls = []
    end_mls = []

    for _, row in phases_df.iterrows():
        start_ml = chrom_df.loc[
            (chrom_df["date_time"] - row["start_time"]).abs().idxmin(), "ml"
        ] if pd.notnull(row["start_time"]) else None

        end_ml = chrom_df.loc[
            (chrom_df["date_time"] - row["end_time"]).abs().idxmin(), "ml"
        ] if pd.notnull(row["end_time"]) else None

        start_mls.append(start_ml)
        end_mls.append(end_ml)

    phases_df["start_ml"] = start_mls
    phases_df["end_ml"] = end_mls

    return phases_df


@app.callback(
    Output("chromatogram-graph", "figure"),
    Output("load-volume-store", "data"),
    Output("x-axis-offset", "data"),
    [
        Input("selected-result-id", "data"),
        Input("left-sensor-dropdown", "value"),
        Input("right-sensor-dropdown", "value"),
        Input("plot-options-checklist", "value"),
    ],
    prevent_initial_call=True
)
def update_chromatogram_plot(result_id, left_sensors, right_sensors, plot_options):
    load_store_data = {}
    fig = go.Figure()
    if not result_id:
        return fig, load_store_data, 0

    qs = AktaChromatogram.objects.filter(result_id=result_id).values()
    df = pd.DataFrame(qs).sort_values(by='ml', ascending=True)
    phases_df = extract_phases(result_id)
    phases_df = fill_phase_mLs(phases_df, df)

    # Optional offset for zeroing x-axis at Sample Application
    offset_ml = 0.0
    sample_app_phase = phases_df[phases_df["label"] == "Sample Application"]
    if not sample_app_phase.empty and pd.notnull(sample_app_phase.iloc[0]["start_ml"]):
        start_ml = sample_app_phase.iloc[0]["start_ml"]
        end_ml = sample_app_phase.iloc[0]["end_ml"]
        load_store_data = {
            "start_ml": round(start_ml, 2),
            "end_ml": round(end_ml, 2),
            "load_volume": round(end_ml - start_ml, 2)
        }
        if "zero_ml" in plot_options:
            offset_ml = sample_app_phase.iloc[0]["start_ml"]
            # Apply offset to chromatogram df
            df["ml"] = df["ml"] - offset_ml
            # Also offset all phase regions
            phases_df["start_ml"] = phases_df["start_ml"] - offset_ml
            phases_df["end_ml"] = phases_df["end_ml"] - offset_ml

    # print(phases_df)
    phases_df.to_csv("debug_phases.csv")

    if df.empty:
        return fig, load_store_data, offset_ml

    phases = []
    for _, row in phases_df.iterrows():
        if pd.notnull(row["start_ml"]) and pd.notnull(row["end_ml"]):
            phases.append({
                "label": row["label"],
                "start": row["start_ml"],
                "end": row["end_ml"]
            })

    left_sensors = left_sensors or []
    right_sensors = right_sensors or []

    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ]

    grid_color = "#eee"
    base_axis_style = dict(
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True,
        ticks="inside",
        tickwidth=1,
        tickcolor="black",
        ticklen=6,
        showgrid=True,
        gridcolor=grid_color,
        minor=dict(
            ticks="inside",
            ticklen=3,
            tickcolor="black",
            showgrid=False
        )
    )

    axis_counter = 1

    # LEFT SENSORS
    for i, sensor in enumerate(left_sensors):
        if sensor not in df.columns:
            continue

        axis_id = "" if axis_counter == 1 else str(axis_counter)
        yaxis_name = f"yaxis{axis_id}"
        yaxis_id = f"y{axis_id}"

        y_data = df[sensor]
        y_min, y_max = y_data.min(), y_data.max()
        if y_min == y_max:
            y_min -= 1
            y_max += 1

        color = default_colors[(axis_counter - 1) % len(default_colors)]

        fig.add_trace(go.Scatter(
            x=df["ml"],
            y=y_data,
            name=AXIS_LABELS.get(sensor, sensor),
            mode="lines",
            yaxis=yaxis_id,
            line=dict(color=color),
            connectgaps=False
        ))

        position_left = 0.0 + 0.05 * i
        if position_left > 0.4:
            position_left = 0.4

        layout_args = {
            **base_axis_style,
            "title": dict(text=AXIS_LABELS.get(sensor, sensor), font=dict(color=color)),
            "side": "left",
            "range": [y_min, y_max]
        }
        if axis_counter > 1:
            layout_args.update({
                "overlaying": "y",
                "anchor": "free",
                "position": position_left
            })

        fig.update_layout(**{yaxis_name: layout_args})
        axis_counter += 1

    # RIGHT SENSORS
    for j, sensor in enumerate(right_sensors):
        if sensor not in df.columns:
            continue

        axis_id = "" if axis_counter == 1 else str(axis_counter)
        yaxis_name = f"yaxis{axis_id}"
        yaxis_id = f"y{axis_id}"

        y_data = df[sensor]
        y_min, y_max = y_data.min(), y_data.max()
        if y_min == y_max:
            y_min -= 1
            y_max += 1

        color = default_colors[(axis_counter - 1) % len(default_colors)]

        fig.add_trace(go.Scatter(
            x=df["ml"],
            y=y_data,
            name=AXIS_LABELS.get(sensor, sensor),
            mode="lines",
            yaxis=yaxis_id,
            line=dict(color=color),
            connectgaps=False
        ))

        position_right = 1.0 - 0.05 * j
        if position_right < 0.6:
            position_right = 0.6

        layout_args = {
            **base_axis_style,
            "title": dict(text=AXIS_LABELS.get(sensor, sensor), font=dict(color=color)),
            "side": "right",
            "range": [y_min, y_max]
        }
        if axis_counter > 1:
            layout_args.update({
                "overlaying": "y",
                "anchor": "free",
                "position": position_right
            })

        fig.update_layout(**{yaxis_name: layout_args})
        axis_counter += 1

    # Add goalpost lines and centered annotations
    for phase in phases:
        midpoint = (phase["start"] + phase["end"]) / 2

        # Start and end vertical lines
        for x_pos in [phase["start"], phase["end"]]:
            fig.add_shape(
                type="line",
                x0=x_pos,
                x1=x_pos,
                yref="paper",
                y0=0.0,
                y1=0.1,
                line=dict(width=1),
                layer="above"
            )

        # Centered label
        fig.add_annotation(
            x=midpoint,
            y=0.05,
            yref="paper",
            text=phase["label"],
            showarrow=False,
            yanchor="bottom",
            xanchor="center",
            font=dict(size=8)
        )
    # Chromatogram information query:
    result = AktaResult.objects.filter(result_id=result_id).first()
    report_name = result.report_name
    cv = result.column_volume
    column_name = result.column_name
    method = result.method
    date = result.date

    # Configure layout including xaxis
    fig.update_layout(
        height=600,
        title=dict(
            text=f"Result: {report_name} - Method: {method} - Column: {column_name} - CV: {cv} mL",
            x=0.5,  # 🔥 center it horizontally
            xanchor='center',
            font=dict(size=12)  # optional: bump font size for readability
        ),
        xaxis={
            **base_axis_style,
            "title": "ml",
            "range": [df["ml"].min(), df["ml"].max()]
        },
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=60, l=60, r=20)
    )

    return fig, load_store_data, offset_ml
