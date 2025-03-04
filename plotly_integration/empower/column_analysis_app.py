from django.db.models import Subquery, OuterRef
from django_plotly_dash import DjangoDash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
from plotly_integration.models import SampleMetadata, TimeSeriesData, PeakResults, EmpowerColumnLogbook, ChromMetadata
import plotly.graph_objects as go
import re
from datetime import datetime
import json
from django.utils.timezone import make_naive, is_aware
import dash_bootstrap_components as dbc

# Initialize the new Dash app
app = DjangoDash('ColumnUsageApp')

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

# ✅ Create preconfigured Figure
injection_figure = go.Figure()

# Configure layout settings
injection_figure.update_layout(
    dragmode="select",  # ✅ Force selection mode
    clickmode="event+select",  # ✅ Capture clicks
    title=dict(
        text="Injection Number vs. Average Pressure & Column Performance",
        x=0.5,
        xanchor='center'),
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
    template="plotly_white"
)

selected_sample_figure = go.Figure()

selected_sample_figure.update_layout(
    title=dict(
        text='Time Series Data for Selected Points',
        x=0.5,
        xanchor='center'),
    xaxis_title='Time',
    yaxis_title='UV280',
    template="plotly_white"
)

# Layout for the new app
app.layout = html.Div([
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

    html.Div([
        html.Div([
            html.Label("Select a Column:", style={'color': '#0056b3', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='column-dropdown',
                placeholder="Select a Column",
                style={'width': '100%', 'margin-bottom': '10px'}
            ),
            html.Label("Select Channel:", style={'color': '#0056b3', 'font-weight': 'bold'}),
            dcc.RadioItems(
                id='channel-radio',
                options=[
                    {'label': 'UV280', 'value': 'channel_1'},
                    {'label': 'UV260', 'value': 'channel_2'},
                    {'label': 'Pressure (psi)', 'value': 'channel_3'}
                ],
                value='channel_1',  # Default to channel 1
                style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'left', 'gap': '10px',
                       'margin-bottom': '10px'}
            ),
            html.Div(
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
                        data=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'center', 'padding': '5px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                    )
                ],
                style={
                    'width': '100%',
                    'padding': '10px',
                    'border': '2px solid #0056b3',
                    'border-radius': '5px',
                    'background-color': '#f7f9fc'
                }
            )
        ], style={
            'width': '100%',
            'padding': '10px',
            'background-color': '#f7f7f7'
        }),
        html.Div([
            # ✅ Wrap `pressure-plot` inside `dcc.Loading`
            dbc.Container([
                # html.H4("Injection Number vs. Average Pressure", style={'text-align': 'center', 'color': '#0056b3'}),
                dcc.Loading(
                    id="loading-pressure-plot",
                    type="circle",  # Other options: "circle", "dot"
                    style={"transform": 'scale(2)', 'text-align': 'center'},
                    overlay_style={"visibility": "visible", "opacity": .5, "backgroundColor": "white"},
                    # custom_spinner=html.H2(["Loading...", dbc.Spinner(color="red")]),
                    children=[
                        dcc.Graph(
                            id='pressure-plot',
                            figure=injection_figure,  # ✅ Set preconfigured figure
                            style={'margin-top': '20px', 'height': '55vh'},
                            config={'clickmode': 'event+select'}
                        )
                    ],
                )
            ], style={'width': '50%', 'padding': '10px'}),

            # ✅ Wrap `pressure-plot` inside `dcc.Loading`
            dbc.Container([
                # html.H4("Sample Plot", style={'text-align': 'center', 'color': '#0056b3'}),
                dcc.Loading(
                    id="loading-clicked-data-plot",
                    type="circle",  # Other options: "circle", "dot"
                    style={"transform": 'scale(2)', 'text-align': 'center'},
                    overlay_style={"visibility": "visible", "opacity": .5, "backgroundColor": "white"},
                    # custom_spinner=html.H2(["Loading...", dbc.Spinner(color="red")]),
                    children=[
                        dcc.Graph(id='clicked-data-graph', figure=selected_sample_figure,
                                  style={'margin-top': '20px', 'height': '55vh'})
                    ],
                )
            ], style={'width': '50%', 'padding': '10px'})],
            style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px', 'width': '100%'}),

        html.Div(className='row', children=[
            html.Div([
                dcc.Markdown("""**Click Data**\n\nClick on points in the graph."""),
                html.Pre(id='click-data', style={**styles['pre'], 'display': 'none'}),
                dcc.Markdown("""**Selection Data**\n\nUse the lasso or rectangle tool to select points."""),
                html.Pre(id='selected-data', style={**styles['pre'], 'display': 'none'}),
                dcc.Markdown("""**Zoom and Relayout Data**\n\nZoom or click on the graph to trigger events."""),
                html.Pre(id='relayout-data', style={**styles['pre'], 'display': 'none'})
            ], style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'space-between', 'width': '100%'})
        ])
    ], style={'display': 'flex',
              'flex-direction': 'column',
              'align-items': 'center',
              'justify-content': 'flex-start',
              'width': '97%'}
    ),
])


@app.callback(
    Output('column-dropdown', 'options'),
    Input('column-dropdown', 'id')
)
def populate_column_dropdown(n_clicks=None):
    """
    Fetch column serial numbers and names from `empower_column_logbook` using Django ORM,
    ensuring we use the pre-stored `most_recent_injection` date.
    """
    # ✅ Retrieve all columns from empower_column_logbook, ordering by most_recent_injection (descending)
    columns = (
        EmpowerColumnLogbook.objects
        .filter(column_serial_number__isnull=False)  # Ensure serial number exists
        .order_by("-most_recent_injection_date")  # Sort by most recent injection date
        .values("id", "column_name", "column_serial_number", "most_recent_injection_date")  # Fetch only needed fields
    )

    column_data = []

    for col in columns:
        serial = col["column_serial_number"]
        column_name = col["column_name"]
        most_recent_injection = col["most_recent_injection_date"]

        # ✅ Format `most_recent_injection` as MM/DD/YYYY HH:MM:SS AM/PM
        if most_recent_injection:
            formatted_date = most_recent_injection.strftime("%m/%d/%Y %I:%M:%S %p")
        else:
            formatted_date = "Unknown"

        # ✅ Store column data
        column_data.append({
            "column_id": col["id"],
            "column_name": column_name,
            "serial_number": serial,
            "date_acquired": formatted_date,
        })

    # ✅ Generate dropdown options
    dropdown_options = [
        {
            'label': f"{col['column_name']} - {col['serial_number']} (Last Used: {col['date_acquired']})",
            'value': col['serial_number']
        }
        for col in column_data
    ]

    return dropdown_options


@app.callback(
    Output('column-sample-table', 'data'),
    Input('column-dropdown', 'value'),
    prevent_initial_call=True
)
def update_sample_count_table(selected_serial_number):
    """
    When a column is selected, update the table using `EmpowerColumnLogbook`.
    """
    if not selected_serial_number:
        return []

    # ✅ Fetch the column entry from EmpowerColumnLogbook
    column_entry = EmpowerColumnLogbook.objects.filter(column_serial_number=selected_serial_number).first()

    if not column_entry:
        return []  # Return empty if no matching column found

    # ✅ Prepare the response data
    table_data = [{
        "column_name": column_entry.column_name,
        "serial_number": column_entry.column_serial_number,
        "sample_count": column_entry.total_injections,  # ✅ Directly use stored injection count
        "most_recent_injection": column_entry.most_recent_injection_date.strftime("%m/%d/%Y") if column_entry.most_recent_injection_date else "Unknown"
    }]

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
    time_cutoff = 18
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


def get_column_performance_data(column_id):
    """
    Fetch column performance data by extracting plate count from the peak results table
    if the sample prefix is 'STD'.
    """
    # Fetch standard samples associated with the selected column
    std_samples = SampleMetadata.objects.filter(
        column_id=column_id,
        sample_prefix="STD"  # ✅ Only process standard samples
    )

    if not std_samples.exists():
        return pd.DataFrame()  # Return empty DataFrame if no standard samples found

    # ✅ Step 1: Store column performance data
    column_performance = []

    for sample in std_samples:
        result_id = sample.result_id
        sample_name = sample.sample_name
        date_acquired = sample.date_acquired

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


def get_data_annotations():
    """
    Fetches sample metadata with pressure-related data from ChromMetadata.
    Uses optimized queries for faster results.
    """
    # ✅ Fetch data with a single query
    data_points = (
        SampleMetadata.objects
        .select_related("chrommetadata")  # ✅ Join with ChromMetadata for efficiency
        .values(
            "sample_name",
            "result_id",
            "chrommetadata__average_pressure",
        )
    )

    # ✅ Process data
    annotated_data = [
        {
            "sample_name": data["sample_name"],
            "result_id": data["result_id"],
            "average_pressure": data["chrommetadata__average_pressure"],
        }
        for data in data_points
    ]

    return annotated_data



@app.callback(
    Output('pressure-plot', 'figure'),
    Input('column-dropdown', 'value'),
    prevent_initial_call=True
)
def update_pressure_plot(selected_serial_number):
    """
    Optimized query: Fetch column_id → Filter SampleMetadata by column_id → Join ChromMetadata efficiently.
    """
    if not selected_serial_number:
        return go.Figure()  # Return an empty figure if no serial number is selected

    # ✅ Step 1: Convert Serial Number to Column ID
    column = EmpowerColumnLogbook.objects.filter(column_serial_number=selected_serial_number).first()
    if not column:
        print(f"⚠ No matching column found for Serial Number: {selected_serial_number}")
        return go.Figure()

    column_id = column.id  # Get the column's ID from EmpowerColumnLogbook

    # ✅ Step 2: Query SampleMetadata using `column_id` (Indexed Foreign Key)
    samples = (
        SampleMetadata.objects
        .filter(column_id=column_id)  # Use column_id for efficient lookup
        .annotate(
            # ✅ Step 3: Use Subquery to pull `average_pressure` from ChromMetadata
            average_pressure=Subquery(
                ChromMetadata.objects
                .filter(result_id=OuterRef("result_id"), system_name=OuterRef("system_name"))
                .values("average_pressure")[:1]  # Only fetch the first matching value
            )
        )
        .values("result_id", "sample_name", "date_acquired", "average_pressure")
    )

    if not samples.exists():
        print(f"⚠ No sample data found for Column ID: {column_id}")
        return go.Figure()

    # ✅ Step 4: Convert to DataFrame for Plotly
    df = pd.DataFrame(list(samples))

    # ✅ Step 5: Sort by `date_acquired` (oldest → newest) and assign injection numbers
    df["date_acquired"] = pd.to_datetime(df["date_acquired"], errors="coerce")
    df = df.sort_values(by="date_acquired").reset_index(drop=True)
    df["injection_number"] = df.index + 1  # Start numbering from 1

    # ✅ Step 6: Prepare Plotly Data
    injection_numbers = df["injection_number"].tolist()
    average_pressures = df["average_pressure"].tolist()
    hover_texts = [
        f"Sample: {row['sample_name']}<br>Date Acquired: {row['date_acquired'].strftime('%m/%d/%Y %I:%M:%S %p')}"
        for _, row in df.iterrows()
    ]

    # ✅ Step 7: Create Plotly Figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=injection_numbers,
        y=average_pressures,
        mode='markers+lines',
        name='Average Pressure',
        customdata=df["result_id"].tolist(),
        text=hover_texts,
        hoverinfo="text+y",
        yaxis="y1",
        marker=dict(color="blue")
    ))

    # ✅ Step 8: Fetch and Overlay Column Performance Data (Plate Count)
    df_performance = get_column_performance_data(column_id)

    if not df_performance.empty:
        df_performance = df_performance[df_performance["peak_name"] == "Peak2-IgG"]

        # Merge injection numbers to maintain consistency
        df_performance = df_performance.merge(df[["result_id", "injection_number"]], on="result_id", how="left")

        # Sort by injection number
        df_performance = df_performance.sort_values(by="injection_number").reset_index(drop=True)

        # Add plate count data to the secondary y-axis
        fig.add_trace(go.Scatter(
            x=df_performance["injection_number"],
            y=df_performance["plate_count"],
            mode="markers+lines",
            name="Peak2-IgG Plate Count",
            marker=dict(color="red"),
            yaxis="y2"
        ))

    # ✅ Step 9: Update Figure Layout
    fig.update_layout(
        dragmode='select',
        clickmode='event+select',
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

    )

    return fig



def filter_primary_axis_points(data):
    if not data:
        return []
    return [point for point in data['points'] if point.get('curveNumber') == 0]  # 0 is primary axis


@app.callback(
    [Output('click-data', 'children'), Output('selected-data', 'children'), Output('clicked-data-graph', 'figure')],
    [Input('pressure-plot', 'clickData'), Input('pressure-plot', 'selectedData'), Input('channel-radio', 'value')]
)
def display_click_data(clickData, selectedData, channel):
    result_ids = []
    filtered_click_data = []  # ✅ Ensure variable is always initialized
    filtered_selected_data = []  # ✅ Ensure variable is always initialized

    print(json.dumps(clickData, indent=2))
    if clickData:
        filtered_click_data = filter_primary_axis_points(clickData)
        # result_ids.append(clickData['points'][0]['customdata'])

    if selectedData:
        # result_ids.extend(point['customdata'] for point in selectedData['points'])
        filtered_selected_data = filter_primary_axis_points(selectedData)

    result_ids = [point['customdata'] for point in (filtered_click_data + filtered_selected_data) if
                  'customdata' in point]

    if not result_ids:
        return go.Figure()

    fig = go.Figure()
    for result_id in set(result_ids):
        time_series = TimeSeriesData.objects.filter(result_id__in=result_ids).values("result_id", "time", channel)
        df = pd.DataFrame(list(time_series))
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        sample_name = sample.sample_name if sample else result_id

        if not df.empty:
            fig.add_trace(go.Scatter(x=df['time'], y=df[channel], mode='lines', name=sample_name))

    channel_names = {
        'channel_1': 'UV280',
        'channel_2': 'UV260',
        'channel_3': 'Pressure (psi)'
    }
    fig.update_layout(title='Time Series Data for Selected Points', xaxis_title='Time',
                      yaxis_title=channel_names.get(channel, channel), template="plotly_white")

    return json.dumps(clickData, indent=2), json.dumps(selectedData, indent=2), fig


@app.callback(
    Output('relayout-data', 'children'),
    Input('pressure-plot', 'relayoutData')
)
def display_relayout_data(relayoutData):
    return json.dumps(relayoutData, indent=2)
