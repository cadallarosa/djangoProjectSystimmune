import pandas as pd
import numpy as np
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly_integration.models import CESDSReport, CESDSMetadata, CESDSTimeSeries
from scipy.signal import find_peaks, savgol_filter, argrelextrema
import dash_bootstrap_components as dbc

app = DjangoDash("CESDSReportViewerApp")

app.layout = html.Div([
    dcc.Store(id="selected-result-ids"),
    dcc.Store(id="reduced-result-ids"),
    dcc.Store(id="nonreduced-result-ids"),

    dcc.Tabs(id="main-tabs", value="tab-select-report", persistence=False, children=[

        # Select Report Tab
        dcc.Tab(label="Select Report", value="tab-select-report", children=[
            html.Div([
                dash_table.DataTable(
                    id="cesds-report-table",
                    columns=[
                        {"name": "Report Name", "id": "report_name"},
                        {"name": "Project ID", "id": "project_id"},
                        {"name": "User ID", "id": "user_id"},
                        {"name": "Date Created", "id": "date_created"},
                        {"name": "Samples", "id": "num_samples"}
                    ],
                    data=[],
                    row_selectable="single",
                    filter_action="native",
                    sort_action="native",
                    page_size=20,
                    style_table={"height": "70vh", "overflowY": "auto"},
                    style_cell={"textAlign": "center", "padding": "8px"},
                    style_header={
                        "backgroundColor": "#e9f1fb",
                        "fontWeight": "bold",
                        "color": "#0047b3",
                        "borderBottom": "2px solid #0047b3"
                    }
                )
            ])
        ]),

        # Reduced Tab
        dcc.Tab(label="Reduced", value="tab-reduced", children=[
            html.Div([
                dcc.Tabs(id="reduced-subtabs", value="tab-reduced-chrom", persistence=True, children=[
                    dcc.Tab(label="Chromatogram", value="tab-reduced-chrom", children=[
                        html.Div(style={"display": "flex"}, children=[
                            html.Div([
                                dcc.Graph(
                                    id="reduced-chromatogram",
                                    config={'responsive': True},
                                    style={"height": "100%"}
                                )
                            ], style={"width": "80%", "padding": "10px", "minHeight": "1000px"}),

                            html.Div([
                                html.H4("Marker Settings"),
                                html.Label("Marker RT (min):"),
                                dcc.Input(id="marker-rt", type="number", value=7, step=0.1, style={"width": "100%"}),

                                html.Label("Marker Label:"),
                                dcc.Input(id="marker-label", type="text", value="10 kDa",
                                          style={"width": "100%", "marginBottom": "20px"}),

                                html.Hr(),
                                html.H4("Peak Detection"),

                                html.Label("Skip Time After Marker (min):"),
                                dcc.Input(id="skip-time", type="number", value=0.3, step=0.05, style={"width": "100%"}),

                                html.Label("Max Peaks:"),
                                dcc.Input(id="max-peaks", type="number", value=4, step=1, min=1,
                                          style={"width": "100%"}),

                                html.Label("Prominence Threshold:"),
                                dcc.Input(id="prominence-threshold", type="number", value=1.0, step=0.01,
                                          style={"width": "100%"}),

                                html.Label("Valley Search Window (min):"),
                                dcc.Input(id="valley-search-window", type="number", value=1, step=0.1,
                                          style={"width": "100%"}),

                                html.Label("Valley Drop Ratio (0–1):"),
                                dcc.Input(id="valley-drop-ratio", type="number", value=0.2, step=0.05, min=0, max=1,
                                          style={"width": "100%"}),

                                html.Label("Smoothing Window (odd integer):"),
                                dcc.Input(id="smoothing-window", type="number", value=11, step=2, min=3,
                                          style={"width": "100%"}),

                                html.Label("Smoothing Polyorder:"),
                                dcc.Input(id="smoothing-polyorder", type="number", value=3, step=1, min=1,
                                          style={"width": "100%", "marginBottom": "20px"}),

                                html.Hr(),
                                html.H4("Light Chain Timing"),
                                html.Button("Calculate Light Chain Time", id="calc-light-chain-btn",
                                            style={"width": "100%", "marginBottom": "10px"}),
                                dcc.Input(id="light-chain-time", type="number", placeholder="Light Chain Time (min)",
                                          readOnly=True, style={"width": "100%"})

                            ], style={"width": "20%", "padding": "10px"})
                        ])
                    ]),
                    dcc.Tab(label="Results Table", value="tab-reduced-table", children=[
                        dash_table.DataTable(
                            id="reduced-table",
                            columns=[],  # will be filled by callback
                            data=[],
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "center"},
                        )
                    ])
                ])
            ])
        ]),

        # Non-Reduced Tab
        dcc.Tab(label="Non-Reduced", value="tab-nonreduced", children=[
            html.Div([
                dcc.Tabs(id="nonreduced-subtabs", value="tab-nonreduced-chrom", persistence=True, children=[
                    dcc.Tab(label="Chromatogram", value="tab-nonreduced-chrom", children=[
                        html.Div(style={"display": "flex"}, children=[
                            html.Div([
                                dcc.Graph(
                                    id="nonreduced-chromatogram",
                                    config={'responsive': False},
                                    # style={"height": "100%"}
                                )
                            ], style={"width": "80%", "padding": "10px", "minHeight": "1000px"}),

                            html.Div([
                                html.H4("Marker Settings"),
                                html.Label("Marker RT (min):"),
                                dcc.Input(id="nr-marker-rt", type="number", value=7, step=0.1, style={"width": "100%"}),

                                html.Label("Marker Label:"),
                                dcc.Input(id="nr-marker-label", type="text", value="10 kDa",
                                          style={"width": "100%", "marginBottom": "20px"}),

                                html.Hr(),
                                html.H4("Peak Detection"),

                                html.Label("Skip Time After Marker (min):"),
                                dcc.Input(id="nr-skip-time", type="number", value=0.3, step=0.05,
                                          style={"width": "100%"}),

                                html.Label("Max Peaks:"),
                                dcc.Input(id="nr-max-peaks", type="number", value=3, step=1, min=1,
                                          style={"width": "100%"}),

                                html.Label("Prominence Threshold:"),
                                dcc.Input(id="nr-prominence-threshold", type="number", value=1.0, step=0.01,
                                          style={"width": "100%"}),

                                html.Label("Valley Search Window (min):"),
                                dcc.Input(id="nr-valley-search-window", type="number", value=3, step=0.1,
                                          style={"width": "100%"}),

                                html.Label("Valley Drop Ratio (0–1):"),
                                dcc.Input(id="nr-valley-drop-ratio", type="number", value=0.2, step=0.05, min=0, max=1,
                                          style={"width": "100%"}),

                                html.Label("Smoothing Window (odd integer):"),
                                dcc.Input(id="nr-smoothing-window", type="number", value=11, step=2, min=3,
                                          style={"width": "100%"}),

                                html.Label("Smoothing Polyorder:"),
                                dcc.Input(id="nr-smoothing-polyorder", type="number", value=3, step=1, min=1,
                                          style={"width": "100%", "marginBottom": "20px"}),

                                html.Label("Intact Time (optional):"),
                                dcc.Input(id="nr-intact-time", type="number", placeholder="Use tallest peak if blank",
                                          style={"width": "100%", "marginBottom": "20px"}),

                            ], style={"width": "20%", "padding": "10px"})
                        ])
                    ]),
                    dcc.Tab(label="Results Table", value="tab-nonreduced-table", children=[
                        dash_table.DataTable(
                            id="nonreduced-table",
                            columns=[],  # will be filled by callback
                            data=[],
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "center"},
                        )
                    ])
                ])
            ])
        ])
    ])
])


@app.callback(
    Output("cesds-report-table", "data"),
    Input("main-tabs", "value")
)
def load_report_table(tab_value):
    if tab_value != "tab-select-report":
        return []
    reports = CESDSReport.objects.order_by("-date_created")
    return [{
        "report_name": r.report_name,
        "project_id": r.project_id,
        "user_id": r.user_id,
        "date_created": r.date_created.strftime("%Y-%m-%d %H:%M"),
        "num_samples": len(r.selected_result_ids.split(","))
    } for r in reports]


@app.callback(
    Output("selected-result-ids", "data"),
    Input("cesds-report-table", "selected_rows"),
    State("cesds-report-table", "data")
)
def store_selected_result_ids(selected_rows, table_data):
    if selected_rows:
        row = table_data[selected_rows[0]]
        report = CESDSReport.objects.filter(report_name=row["report_name"]).first()
        if report:
            return [r.strip() for r in report.selected_result_ids.split(",")]
    return []


@app.callback(
    [Output("reduced-result-ids", "data"),
     Output("nonreduced-result-ids", "data")],
    Input("selected-result-ids", "data")
)
def split_result_ids_by_prefix(result_ids):
    if not result_ids:
        return [], []

    metas = CESDSMetadata.objects.filter(id__in=result_ids)
    reduced = [m.id for m in metas if m.sample_prefix and m.sample_prefix.lower() == "r"]
    nonreduced = [m.id for m in metas if m.sample_prefix and m.sample_prefix.lower() == "nr"]
    return reduced, nonreduced


def detect_valley_to_valley_peaks(
        df,
        signal_col="channel_1",
        time_col="time_min",
        max_peaks=3,
        prominence_threshold=1.0,
        valley_search_window=3.0,
        valley_drop_ratio=0.2,
        smoothing_window=11,
        smoothing_polyorder=3
):
    """
    Detects peaks using valley-to-valley integration with adaptive valley thresholding.
    Returns a list of dictionaries with peak info.
    """
    from scipy.signal import savgol_filter, find_peaks

    time = df[time_col].values
    signal = df[signal_col].values
    smoothed = savgol_filter(signal, window_length=smoothing_window, polyorder=smoothing_polyorder)

    interval = time[1] - time[0]
    min_distance = int(0.3 / interval)
    peak_indices, _ = find_peaks(smoothed, prominence=prominence_threshold, distance=min_distance)

    peak_indices = sorted(peak_indices, key=lambda i: smoothed[i], reverse=True)[:max_peaks]
    peak_indices.sort()

    peak_infos = []

    for idx in peak_indices:
        peak_time = time[idx]
        peak_height = smoothed[idx]
        min_valley_height = peak_height * (1 - valley_drop_ratio)

        left_limit = max(0, idx - int(valley_search_window / interval))
        left_valley_idx = left_limit + np.argmin(smoothed[left_limit:idx])
        left_valley_val = smoothed[left_valley_idx]

        right_limit = min(len(smoothed) - 1, idx + int(valley_search_window / interval))
        right_valley_idx = idx + np.argmin(smoothed[idx:right_limit + 1])
        right_valley_val = smoothed[right_valley_idx]

        if left_valley_val > min_valley_height or right_valley_val > min_valley_height:
            continue

        baseline = np.linspace(left_valley_val, right_valley_val, right_valley_idx - left_valley_idx + 1)
        signal_segment = smoothed[left_valley_idx:right_valley_idx + 1]
        time_segment = time[left_valley_idx:right_valley_idx + 1]
        area = np.trapz(signal_segment - baseline, time_segment)

        if area > 0:
            peak_infos.append({
                "peak_time": time[idx],
                "peak_height": peak_height,
                "area": area,
                "start_time": time[left_valley_idx],
                "end_time": time[right_valley_idx],
                "baseline": baseline,
                "baseline_time": time_segment,
                "peak_index": idx
            })

    return sorted(peak_infos, key=lambda x: x["area"], reverse=True), smoothed


def shade_peak(fig, df, start_time, end_time, baseline, row, col, label, peak_time, peak_height):
    region = df[(df["time_min"] >= start_time) & (df["time_min"] <= end_time)].copy()
    if region.empty:
        return

    fig.add_trace(
        go.Scatter(
            x=np.concatenate([region["time_min"], region["time_min"][::-1]]),
            y=np.concatenate([region["channel_1"], [baseline] * len(region)]),
            fill="toself",
            fillcolor="rgba(0,100,200,0.2)",
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
            hoverinfo="skip"
        ),
        row=row,
        col=col
    )

    fig.add_annotation(
        x=peak_time,
        y=peak_height,
        text=label,
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-30,
        row=row,
        col=col
    )


def generate_chromatogram_figure_advanced(
        result_df_by_id,
        title="Chromatograms",
        marker_rt=None,
        marker_label="10 kDa",
        skip_time=0.3,
        max_peaks=4,
        prominence_threshold=0.05,
        valley_search_window=3.0,
        valley_drop_ratio=0.2,
        smoothing_window=11,
        smoothing_polyorder=3,
        light_chain_time=None,
        table_output=None
):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    num_rows = len(result_df_by_id)
    spacing = 0.05

    fig = make_subplots(
        rows=num_rows, cols=1,
        shared_xaxes=False,
        vertical_spacing=spacing,
        subplot_titles=[meta["sample_id"] for meta in result_df_by_id.values()]
    )

    for i, (mid, meta) in enumerate(result_df_by_id.items(), start=1):
        df = meta["data"]
        if df.empty:
            continue

        fig.add_trace(
            go.Scatter(x=df["time_min"], y=df["channel_1"], mode="lines", name=meta["sample_id"]),
            row=i, col=1
        )

        # Marker annotation
        marker_peak_time = None
        if marker_rt is not None:
            df_marker = df[(df["time_min"] >= marker_rt - 0.5) & (df["time_min"] <= marker_rt + 0.5)]
            if not df_marker.empty:
                idx = df_marker["channel_1"].idxmax()
                marker_peak_time = df_marker.loc[idx, "time_min"]
                peak_height = df_marker.loc[idx, "channel_1"]

                fig.add_annotation(
                    x=marker_peak_time,
                    y=peak_height,
                    text=f"{marker_label} ({marker_peak_time:.2f} min)",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-40,
                    row=i, col=1
                )

        # Peak detection
        df_after_marker = df[df["time_min"] > (marker_peak_time or 0) + skip_time].copy()
        peaks, smoothed = detect_valley_to_valley_peaks(
            df_after_marker,
            signal_col="channel_1",
            time_col="time_min",
            max_peaks=max_peaks,
            prominence_threshold=prominence_threshold,
            valley_search_window=valley_search_window,
            valley_drop_ratio=valley_drop_ratio,
            smoothing_window=smoothing_window,
            smoothing_polyorder=smoothing_polyorder,
        )

        total_area = sum(p["area"] for p in peaks)
        peaks = sorted(peaks, key=lambda x: x["peak_height"], reverse=True)

        light_chain = heavy_chain = None
        if len(peaks) >= 2:
            top2 = peaks[:2]
            if top2[0]["peak_time"] < top2[1]["peak_time"]:
                light_chain, heavy_chain = top2[0], top2[1]
            else:
                light_chain, heavy_chain = top2[1], top2[0]

        percentages = {"LMW": 0.0, "Light Chain": 0.0, "Heavy Chain": 0.0, "HMW": 0.0}

        for p in peaks:
            pct = (p["area"] / total_area * 100) if total_area else 0
            label = f"{pct:.1f}%"
            class_label = None

            if p == light_chain:
                label = f"Light Chain ({pct:.1f}%)"
                class_label = "Light Chain"
            elif p == heavy_chain:
                label = f"Heavy Chain ({pct:.1f}%)"
                class_label = "Heavy Chain"
            elif light_chain and p["peak_time"] < light_chain["peak_time"]:
                label = f"LMW ({pct:.1f}%)"
                class_label = "LMW"
            elif heavy_chain and p["peak_time"] > heavy_chain["peak_time"]:
                label = f"HMW ({pct:.1f}%)"
                class_label = "HMW"
            else:
                continue

            percentages[class_label] += pct

            shade_peak(
                fig, df,
                start_time=p["start_time"],
                end_time=p["end_time"],
                baseline=p["baseline"][0],
                row=i, col=1,
                label=label,
                peak_time=p["peak_time"],
                peak_height=p["peak_height"]
            )

        # Append summary to table output
        if table_output is not None:
            table_output.append({
                "sample_id": meta["sample_id"],
                "LMW": round(percentages["LMW"], 1),
                "Light Chain": round(percentages["Light Chain"], 1),
                "Heavy Chain": round(percentages["Heavy Chain"], 1),
                "HMW": round(percentages["HMW"], 1),
            })

        fig.update_xaxes(title_text="Time (min)", row=i, col=1)
        fig.update_yaxes(title_text="UV", row=i, col=1)

    fig.update_layout(
        height=300 * num_rows,
        title=title,
        showlegend=False,
        template="plotly_white",
        margin=dict(t=40, b=40, l=40, r=30)
    )
    print(f'table output: {table_output}')
    return fig, table_output


@app.callback(
    [Output("reduced-chromatogram", "figure"),
     Output("reduced-table", "data"),
     Output("reduced-table", "columns")],

    [
        Input("reduced-result-ids", "data"),
        Input("marker-rt", "value"),
        Input("marker-label", "value"),
        Input("skip-time", "value"),
        Input("max-peaks", "value"),
        Input("prominence-threshold", "value"),
        Input("valley-search-window", "value"),
        Input("valley-drop-ratio", "value"),
        Input("smoothing-window", "value"),
        Input("smoothing-polyorder", "value"),
        Input("light-chain-time", "value")
    ]
)
def reduced_callback(result_ids, marker_rt, marker_label, skip_time, max_peaks,
                     prominence_threshold, valley_search_window, valley_drop_ratio,
                     smoothing_window, smoothing_polyorder, light_chain_time):
    metas = CESDSMetadata.objects.filter(id__in=result_ids)
    result_df_by_id = {
        str(m.id): {
            "sample_id": m.sample_id_full,
            "data": pd.DataFrame(list(
                CESDSTimeSeries.objects.filter(metadata_id=m.id).values("time_min", "channel_1")
            )).sort_values("time_min")
        }
        for m in metas
    }

    # ✅ Initialize table_output as empty list
    table_output = []

    fig, table_data = generate_chromatogram_figure_advanced(
        result_df_by_id,
        title="Reduced Chromatograms with Peak Classification",
        marker_rt=marker_rt,
        marker_label=marker_label,
        skip_time=skip_time,
        max_peaks=max_peaks,
        prominence_threshold=prominence_threshold,
        valley_search_window=valley_search_window,
        valley_drop_ratio=valley_drop_ratio,
        smoothing_window=smoothing_window,
        smoothing_polyorder=smoothing_polyorder,
        light_chain_time=light_chain_time,
        table_output=table_output
    )
    print(f'table output: {table_output}')
    columns = [{"name": k, "id": k} for k in table_data[0].keys()] if table_data else []
    return fig, table_data, columns


def generate_chromatogram_figure_nonreduced(
        result_df_by_id,
        title="Non-Reduced Chromatograms",
        marker_rt=None,
        marker_label="10 kDa",
        skip_time=0.3,
        max_peaks=4,
        prominence_threshold=0.05,
        valley_search_window=3.0,
        valley_drop_ratio=0.2,
        smoothing_window=11,
        smoothing_polyorder=3,
        intact_time=None,
        table_output=None
):
    num_rows = len(result_df_by_id)
    spacing = 0.05

    fig = make_subplots(
        rows=num_rows, cols=1,
        shared_xaxes=False,
        # vertical_spacing=spacing,
        subplot_titles=[meta["sample_id"] for meta in result_df_by_id.values()]
    )

    for i, (mid, meta) in enumerate(result_df_by_id.items(), start=1):
        df = meta["data"]
        if df.empty:
            continue

        fig.add_trace(
            go.Scatter(x=df["time_min"], y=df["channel_1"], mode="lines", name=meta["sample_id"]),
            row=i, col=1
        )

        marker_peak_time = None
        if marker_rt is not None:
            df_marker = df[(df["time_min"] >= marker_rt - 0.5) & (df["time_min"] <= marker_rt + 0.5)]
            if not df_marker.empty:
                idx = df_marker["channel_1"].idxmax()
                marker_peak_time = df_marker.loc[idx, "time_min"]
                peak_height = df_marker.loc[idx, "channel_1"]

                fig.add_annotation(
                    x=marker_peak_time,
                    y=peak_height,
                    text=f"{marker_label} ({marker_peak_time:.2f} min)",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-40,
                    row=i, col=1
                )

        df_after_marker = df[df["time_min"] > (marker_peak_time or 0) + skip_time].copy()
        peaks, _ = detect_valley_to_valley_peaks(
            df_after_marker,
            signal_col="channel_1",
            time_col="time_min",
            max_peaks=max_peaks,
            prominence_threshold=prominence_threshold,
            valley_search_window=valley_search_window,
            valley_drop_ratio=valley_drop_ratio,
            smoothing_window=smoothing_window,
            smoothing_polyorder=smoothing_polyorder,
        )

        peaks = sorted(peaks, key=lambda x: x["peak_time"])
        total_area = sum(p["area"] for p in peaks)

        # Determine intact peak
        intact = None
        if intact_time:
            closest = min(peaks, key=lambda p: abs(p["peak_time"] - intact_time))
            intact = closest
        elif peaks:
            intact = max(peaks, key=lambda p: p["peak_height"])

        percentages = {"LMW": 0.0, "Light Chain": 0.0, "Intact": 0.0, "HMW": 0.0}

        before_intact = [p for p in peaks if p["peak_time"] < intact["peak_time"]] if intact else []
        after_intact = [p for p in peaks if p["peak_time"] > intact["peak_time"]] if intact else []

        for p in peaks:
            pct = (p["area"] / total_area * 100) if total_area else 0
            class_label = None

            if intact and p["peak_time"] == intact["peak_time"]:
                class_label = "Intact"
            elif p in after_intact:
                class_label = "HMW"
            elif p in before_intact:
                if len(before_intact) == 1:
                    class_label = "LMW"
                elif len(before_intact) >= 2:
                    class_label = "LMW" if p == before_intact[0] else "Light Chain"

            if not class_label:
                continue

            label = f"{class_label} ({pct:.1f}%)"
            percentages[class_label] += pct

            shade_peak(
                fig, df,
                start_time=p["start_time"],
                end_time=p["end_time"],
                baseline=p["baseline"][0],
                row=i, col=1,
                label=label,
                peak_time=p["peak_time"],
                peak_height=p["peak_height"]
            )

        if table_output is not None:
            table_output.append({
                "sample_id": meta["sample_id"],
                "LMW": round(percentages["LMW"], 1),
                "Light Chain": round(percentages["Light Chain"], 1),
                "Intact": round(percentages["Intact"], 1),
                "HMW": round(percentages["HMW"], 1),
            })

        fig.update_xaxes(title_text="Time (min)", row=i, col=1)
        fig.update_yaxes(title_text="UV", row=i, col=1)

    fig.update_layout(
        height=300 * num_rows,
        title=title,
        showlegend=False,
        template="plotly_white",
        margin=dict(t=40, b=40, l=40, r=30)
    )

    return fig, table_output


@app.callback(
    [Output("nonreduced-chromatogram", "figure"),
     Output("nonreduced-table", "data"),
     Output("nonreduced-table", "columns")],
    [
        Input("nonreduced-result-ids", "data"),
        Input("nr-marker-rt", "value"),
        Input("nr-marker-label", "value"),
        Input("nr-skip-time", "value"),
        Input("nr-max-peaks", "value"),
        Input("nr-prominence-threshold", "value"),
        Input("nr-valley-search-window", "value"),
        Input("nr-valley-drop-ratio", "value"),
        Input("nr-smoothing-window", "value"),
        Input("nr-smoothing-polyorder", "value"),
        Input("nr-intact-time", "value")
    ]
)
def nonreduced_callback(result_ids, marker_rt, marker_label, skip_time, max_peaks,
                        prominence_threshold, valley_search_window, valley_drop_ratio,
                        smoothing_window, smoothing_polyorder, intact_time):
    metas = CESDSMetadata.objects.filter(id__in=result_ids)
    result_df_by_id = {
        str(m.id): {
            "sample_id": m.sample_id_full,
            "data": pd.DataFrame(list(
                CESDSTimeSeries.objects.filter(metadata_id=m.id).values("time_min", "channel_1")
            )).sort_values("time_min")
        }
        for m in metas
    }

    table_output = []

    fig, table_data = generate_chromatogram_figure_nonreduced(
        result_df_by_id,
        title="Non-Reduced Chromatograms with Peak Classification",
        marker_rt=marker_rt,
        marker_label=marker_label,
        skip_time=skip_time,
        max_peaks=max_peaks,
        prominence_threshold=prominence_threshold,
        valley_search_window=valley_search_window,
        valley_drop_ratio=valley_drop_ratio,
        smoothing_window=smoothing_window,
        smoothing_polyorder=smoothing_polyorder,
        intact_time=intact_time,
        table_output=table_output
    )

    columns = [{"name": k, "id": k} for k in table_data[0].keys()] if table_data else []
    print(f'table output: {table_output}')

    return fig, table_data, columns
