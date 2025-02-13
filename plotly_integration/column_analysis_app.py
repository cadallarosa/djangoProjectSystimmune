from django_plotly_dash import DjangoDash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
from .models import SampleMetadata, TimeSeriesData, PeakResults
import plotly.graph_objects as go
import re
from datetime import datetime

# Initialize the new Dash app
app = DjangoDash('ColumnUsageApp')

# Layout for the new app
app.layout = html.Div([
    # Top-left Home Button
    html.Div(
        html.Button("Home", id="home-btn", style={
            'background-color': '#0056b3',
            'color': 'white',
            'border': 'none',
            'padding': '10px 20px',
            'font-size': '16px',
            'cursor': 'pointer',
            'border-radius': '5px'
        }),
        style={'margin': '10px'}
    ),

    html.Div([  # Main layout with sidebar and content areas
        html.Div(  # Sidebar
            id='sidebar',
            children=[
                html.H3("Column Usage Tracker", style={
                    'text-align': 'center',
                    'color': '#0056b3',
                    'border-bottom': '2px solid #0056b3',
                    'padding-bottom': '10px'
                }),

                html.Label("Select a Column:", style={'color': '#0056b3', 'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='column-dropdown',
                    placeholder="Select a Column",
                    style={'width': '100%'}
                )
            ],
            style={
                'width': '20%',
                'height': 'calc(100vh - 50px)',
                'background-color': '#f7f7f7',
                'padding': '10px',
                'overflow-y': 'auto',
                'border': '2px solid #0056b3',
                'border-radius': '5px',
                'flex-shrink': '0'
            }
        ),

        html.Div([  # Main content container
            html.Div(  # Table container
                id='table-container',
                children=[
                    html.H4("Column Sample Usage", style={'text-align': 'center', 'color': '#0056b3'}),

                    dash_table.DataTable(
                        id='column-sample-table',
                        columns=[
                            {"name": "Column Name", "id": "column_name"},
                            {"name": "Serial Number", "id": "serial_number"},
                            {"name": "Sample Count", "id": "sample_count"}
                        ],
                        data=[],  # Will be dynamically updated
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'center', 'padding': '5px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                    )
                ],
                style={
                    'width': '68%',
                    'padding': '10px',
                    'border': '2px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#f7f9fc',
                    'margin-bottom': '10px'
                }
            ),

            html.Div(  # Graph container
                id='graph-container',
                children=[
                    html.H4("Injection Number vs. Average Pressure",
                            style={'text-align': 'center', 'color': '#0056b3'}),
                    dcc.Graph(
                        id='pressure-plot',
                        figure={},
                        style={'margin-top': '20px'                        }

                    )
                ],
                style={
                    'width': '68%',
                    'padding': '10px',
                    'border': '2px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#f7f9fc'
                }
            )
        ], style={'width': '80%', 'padding': '10px', 'overflow-y': 'auto'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'})
])

def get_date_acquired_by_result_id(result_id):
    """
    Fetch the `date_acquired` for a given result_id.
    SQLite stores it as TEXT, so we need to parse and format it.
    Returns it in MM/DD/YYYY HH:MM:SS AM/PM format.
    """
    raw_date = SampleMetadata.objects.filter(result_id=result_id).values_list("date_acquired", flat=True).first()

    if not raw_date or raw_date.strip() == "":
        return "Unknown"  # Default if missing

    try:
        # ✅ Parse SQLite's text format (YYYY-MM-DD HH:MM:SS+00:00)
        parsed_date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S%z")

        # ✅ Format into MM/DD/YYYY HH:MM:SS AM/PM
        return parsed_date.strftime("%m/%d/%Y %I:%M:%S %p")

    except ValueError:
        print(f"⚠ Error parsing date for Result ID '{result_id}': {raw_date}")
        return "Unknown"


@app.callback(
    Output('column-dropdown', 'options'),
    Input('column-dropdown', 'id')
)
def populate_column_dropdown(_):
    """
    Fetch unique column serial numbers from SampleMetadata,
    ensuring that we use the latest `date_acquired`.
    Uses `get_date_acquired_by_result_id()` to format the date properly.
    """
    # Fetch all unique column serial numbers with associated result_id
    unique_columns = (
        SampleMetadata.objects
        .filter(column_serial_number__isnull=False)  # Exclude NULL serial numbers
        .values("column_name", "column_serial_number", "result_id")  # Fetch necessary fields
    )

    column_data = {}

    for col in unique_columns:
        serial = col["column_serial_number"]
        column_name = col["column_name"]
        result_id = col["result_id"]

        # ✅ Use `get_date_acquired_by_result_id()` to fetch formatted date
        formatted_date = get_date_acquired_by_result_id(result_id)

        # ✅ Ensure consistent formatting for comparison
        parsed_date = pd.to_datetime(formatted_date, errors="coerce") if formatted_date != "Unknown" else None

        # ✅ Store only the most recent `date_acquired` for each `serial_number`
        if serial not in column_data or (parsed_date and parsed_date > column_data[serial]["parsed_date"]):
            column_data[serial] = {
                "column_name": column_name,
                "serial_number": serial,
                "date_acquired": formatted_date,
                "parsed_date": parsed_date  # Store parsed date for sorting
            }

    # ✅ Step 1: Convert `column_data` to a list
    column_list = list(column_data.values())

    # ✅ Step 2: Sort by `date_acquired` descending, placing "Unknown" at the bottom
    column_list.sort(
        key=lambda x: (x["parsed_date"] is None, x["parsed_date"] if x["parsed_date"] else pd.Timestamp.min),
        reverse=True  # Sort by date descending
    )

    # ✅ Step 3: Generate dropdown options
    dropdown_options = [
        {
            'label': f"{col['column_name']} - {col['serial_number']} (Last Used: {col['date_acquired']})",
            'value': col['serial_number']
        }
        for col in column_list
    ]

    return dropdown_options


@app.callback(
    Output('column-sample-table', 'data'),
    Input('column-dropdown', 'value'),
    prevent_initial_call=True
)
def update_sample_count_table(selected_serial_number):
    """
    When a column is selected, update the table with ordered injection data.
    Ensures data is sorted by `date_acquired` (most recent → oldest).
    """
    if not selected_serial_number:
        return []

    # Fetch all samples for the selected column
    samples = SampleMetadata.objects.filter(column_serial_number=selected_serial_number)

    if not samples.exists():
        return []

    # ✅ Step 1: Store sample data in a list
    sample_data = []
    for sample in samples:
        formatted_date = get_date_acquired_by_result_id(sample.result_id)  # ✅ Use result_id for consistency

        sample_data.append({
            "column_name": sample.column_name,
            "serial_number": sample.column_serial_number,
            "result_id": sample.result_id,
            "date_acquired": formatted_date
        })

    # ✅ Step 2: Convert to DataFrame
    df = pd.DataFrame(sample_data)

    if df.empty:
        return []  # Return empty table if no data

    # ✅ Step 3: Convert `date_acquired` to datetime, handling missing values
    df["date_acquired"] = pd.to_datetime(df["date_acquired"], errors="coerce")

    # ✅ Step 4: Sort by `date_acquired` (Most Recent → Oldest)
    df = df.sort_values(by="date_acquired", ascending=False).reset_index(drop=True)

    # ✅ Step 5: Assign injection numbers based on sorted order
    df["injection_number"] = df.index + 1  # Start numbering from 1

    # ✅ Step 6: Count total injections per column
    sample_count = len(df)

    # ✅ Step 7: Ensure table updates correctly
    table_data = [
        {
            "column_name": df["column_name"].iloc[0] if not df.empty else "Unknown",
            "serial_number": selected_serial_number,
            "sample_count": sample_count
        }
    ]

    return table_data


def get_top_peaks(result_id):
    """
    Fetch and process the top 5 peaks by area for a given standard result ID.
    Returns a DataFrame with ordered peak names and plate counts.
    """
    # Fetch peak results
    peaks = PeakResults.objects.filter(result_id=result_id).values(
        "peak_name", "peak_retention_time", "height", "area", "asym_at_10", "plate_count", "res_hh"
    )
    df = pd.DataFrame(list(peaks))

    if df.empty:
        return df  # Return empty DataFrame if no peaks found

    # ✅ Filter by retention time cutoff
    time_cutoff = 15.5
    df = df[df["peak_retention_time"] <= time_cutoff]

    # ✅ Define ordered peak names
    ordered_peak_names = [
        "Peak1-Thyroglobulin",
        "Peak2-IgG",
        "Peak3-BSA",
        "Peak4-Myoglobin",
        "Peak5-Uracil"
    ]

    # ✅ Step 1: Sort peaks by area (descending) and keep only the top 5
    df = df.sort_values(by="area", ascending=False).reset_index(drop=True)
    df = df.iloc[:5] if len(df) > 5 else df

    # ✅ Step 2: Reorder the selected peaks by retention time (ascending)
    df = df.sort_values(by="peak_retention_time", ascending=True).reset_index(drop=True)

    # ✅ Step 3: Assign peak names from ordered list
    df["peak_name"] = ordered_peak_names[:len(df)]

    return df

def get_column_performance_data(selected_serial_number):
    """
    Fetch column performance data by extracting plate count from the peak results table
    if the sample prefix is 'STD'.
    """
    # Fetch standard samples associated with the selected column
    std_samples = SampleMetadata.objects.filter(
        column_serial_number=selected_serial_number,
        sample_prefix="STD"  # ✅ Only process standard samples
    )

    if not std_samples.exists():
        return pd.DataFrame()  # Return empty DataFrame if no standard samples found

    # ✅ Step 1: Store column performance data
    column_performance = []

    for sample in std_samples:
        result_id = sample.result_id
        sample_name = sample.sample_name
        date_acquired = get_date_acquired_by_result_id(result_id)

        # ✅ Get peak results for the standard
        df_peaks = get_top_peaks(result_id)

        if df_peaks.empty:
            continue  # Skip if no peak results found

        # ✅ Step 2: Only keep `Peak2-IgG`
        df_peaks = df_peaks[df_peaks["peak_name"] == "Peak2-IgG"]

        # ✅ Store plate count data
        for _, row in df_peaks.iterrows():
            column_performance.append({
                "result_id": result_id,  # Store result_id to match injection number later
                "sample_name": sample_name,
                "date_acquired": date_acquired,
                "peak_name": row["peak_name"],
                "plate_count": row["plate_count"]
            })

    # ✅ Step 3: Convert to DataFrame
    df_performance = pd.DataFrame(column_performance)

    return df_performance


@app.callback(
    Output('pressure-plot', 'figure'),
    Input('column-dropdown', 'value'),
    prevent_initial_call=True
)
def update_pressure_plot(selected_serial_number):
    """
    Plot Injection Number vs. Average Pressure at the Midpoint of Each Run.
    Overlay Column Performance (Plate Count) on a secondary Y-axis.
    """
    if not selected_serial_number:
        return go.Figure()

    # Fetch all samples with the selected column serial number
    samples = SampleMetadata.objects.filter(column_serial_number=selected_serial_number)

    if not samples.exists():
        return go.Figure()

    # ✅ Step 1: Store sample data in a DataFrame using `result_id`
    sample_data = []
    for sample in samples:
        formatted_date = get_date_acquired_by_result_id(sample.result_id)

        sample_data.append({
            "result_id": sample.result_id,
            "date_acquired": formatted_date
        })

    # ✅ Step 2: Convert to DataFrame and sort by `date_acquired` (oldest → newest)
    df = pd.DataFrame(sample_data)
    df["date_acquired"] = pd.to_datetime(df["date_acquired"], errors="coerce")
    df = df.sort_values(by="date_acquired").reset_index(drop=True)

    # ✅ Step 3: Assign injection numbers based on sorted order
    df["injection_number"] = df.index + 1  # Start numbering from 1

    # ✅ Step 4: Prepare lists for plotting
    injection_numbers = []
    average_pressures = []
    hover_texts = []

    for _, row in df.iterrows():
        result_id = row["result_id"]
        injection_number = row["injection_number"]
        date_acquired = row["date_acquired"].strftime("%m/%d/%Y %I:%M:%S %p")

        # ✅ Fetch sample name using `result_id`
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            continue

        sample_name = sample.sample_name
        run_time = sample.run_time  # Now a float, no need for regex extraction

        # ✅ Validate `run_time` as a float
        if isinstance(run_time, (int, float)) and run_time > 0:
            midpoint_time = run_time / 2  # Compute midpoint directly
        else:
            print(f"⚠ Skipping Sample '{sample_name}' - Invalid run_time: {sample.run_time}")
            continue

        # Get pressure data for Channel 3
        pressure_data = list(TimeSeriesData.objects.filter(result_id=result_id).values("time", "channel_3"))

        if not pressure_data:
            print(f"⚠ No pressure data found for Sample '{sample_name}'")
            continue

        # Convert to DataFrame and sort by time
        df_pressure = pd.DataFrame(pressure_data).sort_values(by="time")

        # Find closest time index to midpoint
        closest_idx = (df_pressure["time"] - midpoint_time).abs().idxmin()

        # Select 10 points before and after (ensure bounds)
        start_idx = max(closest_idx - 10, 0)
        end_idx = min(closest_idx + 10, len(df_pressure) - 1)

        # Compute average pressure in the range
        avg_pressure = df_pressure.loc[start_idx:end_idx, "channel_3"].mean()

        # ✅ Store data for the plot
        injection_numbers.append(injection_number)
        average_pressures.append(avg_pressure)
        hover_texts.append(f"Sample: {sample_name}<br>Date Acquired: {date_acquired}")

    # ✅ Step 5: Fetch Column Performance Data for `Peak2-IgG`
    df_performance = get_column_performance_data(selected_serial_number)

    if not df_performance.empty:
        df_performance = df_performance[df_performance["peak_name"] == "Peak2-IgG"]

        # Merge injection numbers to maintain consistency
        df_performance = df_performance.merge(df[["result_id", "injection_number"]], on="result_id", how="left")

        # ✅ Ensure missing injections are filled properly
        df_performance["injection_number"] = df_performance["injection_number"].astype("Int64")

        # ✅ Sort by injection number
        df_performance = df_performance.sort_values(by="injection_number").reset_index(drop=True)

    # ✅ Step 6: Create the Plotly Figure
    fig = go.Figure()

    # 🔹 **Plot Average Pressure on Primary Y-axis**
    fig.add_trace(go.Scatter(
        x=injection_numbers,
        y=average_pressures,
        mode='markers+lines',
        name='Average Pressure',
        text=hover_texts,
        hoverinfo="text+y",
        yaxis="y1",  # Assign to primary Y-axis
        marker=dict(color="blue")
    ))

    # 🔹 **Plot Column Performance (Plate Count) on Secondary Y-axis**
    if not df_performance.empty:
        fig.add_trace(go.Scatter(
            x=df_performance["injection_number"],
            y=df_performance["plate_count"],
            mode="markers+lines",
            name="Peak2-IgG Plate Count",
            marker=dict(color="red"),
            yaxis="y2"  # Assign to secondary Y-axis
        ))

    # ✅ Step 7: Update Layout with Dual Y-axes and Legend
    fig.update_layout(
        title="Injection Number vs. Average Pressure & Column Performance",
        xaxis_title="Injection Number",
        showlegend=False,
        yaxis=dict(
            title="Average Pressure (psi)",
            side="left",
            color="blue"
        ),
        yaxis2=dict(
            title="Plate Count (Peak2-IgG)",
            overlaying="y",
            side="right",
            showgrid=False,
            color="red"
        ),
        template="plotly_white",
        # legend=dict(
        #     x=1.05,  # 🔹 Moves legend just outside the graph
        #     y=1,  # 🔹 Aligns legend at the top
        #     xanchor="left",  # 🔹 Ensures it stays outside the plot
        #     yanchor="top",  # 🔹 Keeps it at the top
        #     bgcolor="rgba(255,255,255,0.8)",  # 🔹 Optional: White background for clarity
        #     bordercolor="rgba(0,0,0,0.2)",  # 🔹 Optional: Light border for definition
        #     borderwidth=1
        # )
    )

    return fig
