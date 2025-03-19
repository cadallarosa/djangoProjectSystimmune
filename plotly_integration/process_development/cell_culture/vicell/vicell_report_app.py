import dash
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, MATCH, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
from plotly_integration.models import ViCellData, ViCellReport
import json
from datetime import datetime
import re
import plotly.express as px

# Initialize the Dash app
app = DjangoDash("ViCellReportApp")

# Define the variables and their corresponding labels
VARIABLES = {
    "cell_count": "Total Cell Count",
    # "viable_cells": "Viable Cell Count",
    # "total_cells_per_ml": "Total Cells/mL",
    "viable_cells_per_ml": "Viable Cells/mL",
    "viability": "Viability (%)",
    # "average_diameter": "Average Diameter (µm)",
    "average_viable_diameter": "Average Viable Diameter (µm)",
    # "average_circularity": "Average Circularity",
    # "average_viable_circularity": "Average Viable Circularity"
}

# ✅ Define initial column structure
INITIAL_COLUMNS = [
    {"name": "Sample ID", "id": "sample_id"},
    {"name": "Date", "id": "date_time"},
    {"name": "Process Day", "id": "day"},
    {"name": "Process Time (hr)", "id": "process_time_hours"},
    # {"name": "Total Cell Count", "id": "cell_count"},
    # {"name": "Viable Cell Count", "id": "viable_cells"},
    {"name": "Total Cells/mL", "id": "total_cells_per_ml"},
    {"name": "Viable Cells/mL", "id": "viable_cells_per_ml"},
    {"name": "Viability (%)", "id": "viability"},
    # {"name": "Avg Diameter (µm)", "id": "average_diameter"},
    {"name": "Avg Viable Diameter (µm)", "id": "average_viable_diameter"},
    # {"name": "Avg Circularity", "id": "average_circularity"},
    # {"name": "Avg Viable Circularity", "id": "average_viable_circularity"}
    {"name": "Cumulative Generations", "id": "cumulative_generations"},
    {"name": "Doubling Time (hrs)", "id": "doubling_time"}

]

app.layout = html.Div(
    style={"display": "flex", "flexDirection": "column", "height": "100vh", "padding": "20px"},
    children=[
        dcc.Store(id='selected-report', data=None),  # ✅ Store for selected report ID

        html.H1("Vi Cell Report", style={"textAlign": "center", "color": "#0047b3", "marginBottom": "20px"}),

        # ✅ Report Selection Dropdown
        html.Label("Select a Report:", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id="report-dropdown",
            options=[],  # ✅ Populated dynamically
            placeholder="Select a report...",
            style={"width": "50%", "marginBottom": "20px"}
        ),

        # ✅ Tabs for variable selection
        dcc.Tabs(
            id="variable-tabs",
            value="cell_count",
            children=[dcc.Tab(label=label, value=var) for var, label in VARIABLES.items()]
                     + [  # ✅ Append extra tab
                         dcc.Tab(label="Summary", value="summary")
                     ]
        ),

        # ✅ Graph container that expands to fill remaining space
        html.Div(
            id="variable-graph-container",
            style={"flexGrow": 1, "display": "flex", "justifyContent": "center", "alignItems": "center"},
            children=[dcc.Graph(
                figure=[],
                style={"height": "90%", "width": "100%"},
                config={"responsive": True}
            )]
        ),
        # ✅ New dropdown & table container (only visible in "Summary" tab)
        html.Div(
            id="summary-container",
            style={
                "marginTop": "0px",  # ✅ Aligns container at the top
                "display": "none",  # ✅ Hide initially
                "position": "relative",  # ✅ Ensures it stays in the normal flow
                "width": "95%",  # ✅ Ensures it spans the full width
                "justifyContent": "flex-start",  # ✅ Aligns content at the top
                "alignItems": "flex-start",  # ✅ Ensures child elements start at the top
                "padding": "10px 0",  # ✅ Adds slight spacing for better layout
            },
            children=[
                dcc.Dropdown(
                    id="subset-dropdown",
                    placeholder="Select a Reactor Number",
                    style={"width": "50%", "marginBottom": "10px"}  # ✅ Adjust spacing
                ),
                html.Br(),

                # ✅ Initialize DataTable with column names & styles
                dash_table.DataTable(
                    id="subset-table",
                    data=[],  # ✅ Empty but structured data
                    columns=INITIAL_COLUMNS,  # ✅ Predefined columns
                    style_table={
                        "overflowX": "auto",  # ✅ Prevents horizontal scrolling
                        "width": "100%",  # ✅ Ensures it doesn't stretch too much
                        "maxWidth": "100%",  # ✅ Limits max width for better centering
                        "margin": "auto",  # ✅ Centers the table horizontally
                        "display": "flex",
                        "justifyContent": "center",
                        "borderRadius": "8px",
                        "table-layout": "fixed"
                    },
                    style_header={
                        "backgroundColor": "#e9f1fb",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "color": "#0047b3"
                    },
                    style_cell={
                        "textAlign": "center",
                        "padding": "10px",
                        "borderBottom": "1px solid #ccc",
                        "fontFamily": "Arial, sans-serif"
                    },
                    style_data={"backgroundColor": "white", "color": "#333"},
                    filter_action="native",
                    sort_action="native"
                ),
            ]
        ),
    ]
)


# Populate Report Dropdown
@app.callback(
    Output("report-dropdown", "options"),
    Output("report-dropdown", "value"),
    Input("report-dropdown", "value")
)
def populate_report_dropdown(selected_report):
    reports = ViCellReport.objects.all().order_by("-date_created")

    if not reports:
        return [], None

    options = [
        {"label": f"{r.report_name} (Created: {r.date_created.strftime('%Y-%m-%d %H:%M:%S')})", "value": r.id}
        for r in reports
    ]

    default_value = selected_report if selected_report else reports[0].id
    return options, default_value


def process_and_sort_samples(sample_names):
    """
    - Fetches parsed data from the ViCellData table instead of re-parsing.
    - Groups by `sample_id` and queries ViCellData to get data.
    - Returns a separate DataFrame for each unique `experiment`.
    """

    # ✅ Query `ViCellData` for multiple samples at once
    samples = ViCellData.objects.filter(sample_id__in=sample_names).values(
        "sample_id", "experiment", "day", "reactor_type", "reactor_number", "special",
        "date_time", "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
        "viability", "average_diameter", "average_viable_diameter", "average_circularity",
        "average_viable_circularity"
    )

    df = pd.DataFrame(list(samples))

    if df.empty:
        print("⚠️ No valid samples found.")
        return {}

    # ✅ Sort by reactor number, day, and special condition
    df_sorted = df.sort_values(by=["reactor_number", "day", "special"], ascending=[True, True, True])

    # ✅ Group by `reactor_number` to organize data properly
    sample_groups = df_sorted.groupby("reactor_number")["sample_id"].apply(list).to_dict()

    grouped_data = {}

    for reactor_number, result_names in sample_groups.items():
        print(f"🔍 Querying ViCellData for Reactor Number: {reactor_number}, Samples: {result_names}")  # Debugging log

        # ✅ Fetch ViCellData for the grouped samples
        vicell_data = ViCellData.objects.filter(sample_id__in=result_names).values(
            "sample_id", "day", "date_time", "cell_count", "viable_cells", "total_cells_per_ml",
            "viable_cells_per_ml", "viability", "average_diameter", "average_viable_diameter",
            "average_circularity", "average_viable_circularity", "reactor_type"
        )

        vicell_df = pd.DataFrame(list(vicell_data))

        if not vicell_df.empty:
            grouped_data[reactor_number] = vicell_df  # ✅ Store the queried results
        else:
            print(f"⚠️ No matching data found for Reactor Number {reactor_number}")
            grouped_data[reactor_number] = pd.DataFrame(
                columns=["sample_id", "day", "date_time", "cell_count", "viable_cells",
                         "total_cells_per_ml", "viable_cells_per_ml", "viability", "average_diameter",
                         "average_viable_diameter", "average_circularity", "average_viable_circularity",
                         "reactor_type"]
            )  # ✅ Empty DataFrame with column names

    return grouped_data  # ✅ `{reactor_number: DataFrame}`


@app.callback(
    Output("variable-graph-container", "children"),
    [Input("report-dropdown", "value"),
     Input("variable-tabs", "value")],
    prevent_initial_call=True
)
def update_graph(selected_report_id, selected_variable):
    """
    Updates the graph based on the selected variable tab.
    Each graph plots different `reactor_number` groups over time using `day` as the x-axis.
    """
    if selected_variable is None:
        return "⚠️ No variable selected."
    if selected_variable == 'summary':
        return None
    if not selected_report_id:
        return "⚠️ No report selected."

    report = ViCellReport.objects.filter(id=selected_report_id).first()
    if not report:
        return "⚠️ Report not found."

    if not report.selected_result_ids:
        return "⚠️ No selected result IDs found in this report."

    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]
    sample_names = list(ViCellData.objects.filter(id__in=sample_ids).values_list("sample_id", flat=True))

    if not sample_names:
        return "⚠️ No valid sample names found."

    # ✅ Process and group by `reactor_number`
    sorted_groups = process_and_sort_samples(sample_names)

    fig = px.line()

    for reactor_number, df in sorted_groups.items():
        if not df.empty and selected_variable in df.columns:
            print(df)
            df_sorted = df

            # ✅ Drop NaN/None values for the selected variable
            df_sorted = df.dropna(subset=[selected_variable])

            # ✅ Ensure there's still data left after dropping NaN values
            if df_sorted.empty:
                print(f"⚠️ All values were NaN for {selected_variable} in Reactor {reactor_number}, skipping...")
                continue  # Skip this reactor if no data remains

            # ✅ Get the unique reactor type for this group
            reactor_type = df_sorted["reactor_type"].iloc[0] if "reactor_type" in df_sorted.columns else "Unknown"

            fig.add_scatter(
                x=df_sorted["day"],
                y=df_sorted[selected_variable],
                mode="lines+markers",
                text=df_sorted["sample_id"],  # ✅ Display sample name on each point
                textposition="top center",
                name=f"{reactor_type}{int(reactor_number)}"
            )

    fig.update_layout(
        title={
            "text": f"{VARIABLES[selected_variable]}",
            "x": 0.5,  # ✅ Centers the title
            "xanchor": "center",
            "yanchor": "top"
        },
        # xaxis=dict(range=[0, None]),  # ✅ Start x-axis at 0
        xaxis_title="Day",
        yaxis_title=f"{VARIABLES[selected_variable]}",
        legend_title="Reactor Number",

        # height=800,  # ✅ Dynamically adjust height
        # margin={"l": 40, "r": 40, "t": 60, "b": 40},  # ✅ Reduce margins to maximize space
        # autosize=True  # ✅ Allow figure to resize dynamically
    )

    return dcc.Graph(figure=fig, style={"height": "90%", "width": "100%"}, )


# Summary Tab Logic

@app.callback(
    [Output("summary-container", "style"),
     Output("variable-graph-container", "style")],
    [Input("variable-tabs", "value")]
)
def toggle_tabs(selected_tab):
    """ Show summary content only when 'Summary' tab is selected and hide graph container. """

    # ✅ When "Summary" is selected, show summary container & hide graph container
    if selected_tab == "summary":
        summary_style = {"marginTop": "20px", "display": "block"}
        graph_style = {"flexGrow": 1, "display": "none", "justifyContent": "center", "alignItems": "center"}

    # ✅ Otherwise, show graph container & hide summary container
    else:
        summary_style = {"marginTop": "20px", "display": "none"}
        graph_style = {"flexGrow": 1, "display": "flex", "justifyContent": "center", "alignItems": "center"}

    return summary_style, graph_style


@app.callback(
    [Output("subset-dropdown", "options"),
     Output("subset-dropdown", "value")],  # ✅ Auto-select first option
    Input("report-dropdown", "value")
)
def update_reactor_number_dropdown(selected_report_id):
    """ Populate dropdown with available reactor numbers from the selected report. """
    if not selected_report_id:
        return []

    report = ViCellReport.objects.filter(id=selected_report_id).first()
    if not report or not report.selected_result_ids:
        return []

    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]

    # ✅ Query all distinct reactor numbers, ignoring NULL values
    reactors = list(
        ViCellData.objects.filter(id__in=sample_ids, reactor_number__isnull=False)
        .values_list("reactor_number", flat=True)
        .distinct()
    )

    reactor_type = list(
        ViCellData.objects.filter(id__in=sample_ids, reactor_number__isnull=False)
        .values_list("reactor_type", flat=True)
        .distinct()
    )

    # ✅ Debugging: Check if reactors were retrieved
    print("Retrieved Reactors:", reactors)

    # ✅ Ensure reactors are sorted numerically
    sorted_reactors = sorted(filter(lambda x: x is not None, reactors))

    if not sorted_reactors:
        print("⚠️ No reactor numbers found!")

    # ✅ Create dropdown options
    options = [{"label": f"Reactor {reactor}", "value": reactor} for reactor in sorted_reactors]

    return options, sorted_reactors[0]


# @app.callback(
#     Output("subset-table", "data"),
#     [Input("subset-dropdown", "value"),
#      Input("report-dropdown", "value")]
# )
# def update_summary_table(selected_reactor, selected_report_id):
#     """ Populate table with data when a reactor number is selected from the selected report. """
#     if not selected_report_id or not selected_reactor:
#         print("⚠️ No reactor or report selected.")
#         return []
#
#     # ✅ Fetch the selected report
#     report = ViCellReport.objects.filter(id=selected_report_id).first()
#     if not report or not report.selected_result_ids:
#         print("⚠️ Report not found or contains no selected results.")
#         return []
#
#     # ✅ Extract sample IDs associated with the report
#     sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]
#     print(f"🔍 Selected Sample IDs: {sample_ids}")
#
#     if not sample_ids:
#         print("⚠️ No sample IDs found in the selected report.")
#         return []
#
#     # ✅ Ensure `selected_reactor` is an integer
#     try:
#         selected_reactor = int(selected_reactor)
#     except ValueError:
#         print(f"⚠️ Reactor number '{selected_reactor}' is not a valid integer.")
#         return []
#
#     # ✅ Query by `reactor_number` and `sample_id`
#     subset_data = ViCellData.objects.filter(id__in=sample_ids, reactor_number=selected_reactor).values(
#         "date_time", "sample_id", "day", "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
#         "viability", "average_diameter", "average_viable_diameter", "average_circularity", "average_viable_circularity"
#     )
#
#     subset_data_list = list(subset_data)
#
#     # ✅ Debugging: Check if data was retrieved
#     print(f"✅ Found {len(subset_data_list)} rows for Reactor {selected_reactor}.")
#     print(subset_data_list[:5])  # Print first 5 rows to verify structure
#
#     if not subset_data_list:
#         print(f"⚠️ No data found for Reactor {selected_reactor} in the selected report.")
#         return []
#
#     # ✅ Convert to DataFrame for better formatting
#     df = pd.DataFrame(subset_data_list)
#
#     if df.empty:
#         print("⚠️ DataFrame is empty after conversion.")
#         return []
#
#     # ✅ Convert datetime column to string for display
#     if "date_time" in df.columns:
#         df["date_time"] = df["date_time"].astype(str)
#
#     # ✅ Return updated data and column headers
#     return df.to_dict("records")


@app.callback(
    Output("subset-table", "data"),
    [Input("subset-dropdown", "value"),
     Input("report-dropdown", "value")]
)
def update_summary_table(selected_reactor, selected_report_id):
    """ Populate table with data when a reactor number is selected from the selected report. """
    if not selected_report_id or not selected_reactor:
        print("⚠️ No reactor or report selected.")
        return []

    # ✅ Fetch the selected report
    report = ViCellReport.objects.filter(id=selected_report_id).first()
    if not report or not report.selected_result_ids:
        print("⚠️ Report not found or contains no selected results.")
        return []

    # ✅ Extract sample IDs associated with the report
    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]
    print(f"🔍 Selected Sample IDs: {sample_ids}")

    if not sample_ids:
        print("⚠️ No sample IDs found in the selected report.")
        return []

    # ✅ Ensure `selected_reactor` is an integer
    try:
        selected_reactor = int(selected_reactor)
    except ValueError:
        print(f"⚠️ Reactor number '{selected_reactor}' is not a valid integer.")
        return []

    # ✅ Query by `reactor_number` and `sample_id`
    subset_data = ViCellData.objects.filter(id__in=sample_ids, reactor_number=selected_reactor).values(
        "date_time", "sample_id", "day", "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
        "viability", "average_diameter", "average_viable_diameter", "average_circularity", "average_viable_circularity"
    )

    subset_data_list = list(subset_data)

    # ✅ Debugging: Check if data was retrieved
    print(f"✅ Found {len(subset_data_list)} rows for Reactor {selected_reactor}.")
    print(subset_data_list[:5])  # Print first 5 rows to verify structure

    if not subset_data_list:
        print(f"⚠️ No data found for Reactor {selected_reactor} in the selected report.")
        return []

    # ✅ Convert to DataFrame for better formatting
    df = pd.DataFrame(subset_data_list)

    if df.empty:
        print("⚠️ DataFrame is empty after conversion.")
        return []

    # Ensure date_time column is in datetime format and timezone-naive
    df["date_time"] = pd.to_datetime(df["date_time"], errors='coerce').dt.tz_localize(None)

    # Extract Day 0 time and ensure it is timezone-naive
    day_0_row = df[df["day"] == 0]
    if not day_0_row.empty:
        day_0_time = day_0_row["date_time"].values[0]
        if pd.notna(day_0_time):
            day_0_time = pd.to_datetime(day_0_time).tz_localize(None)
    else:
        print("⚠️ No Day 0 found, unable to calculate process time.")
        return []

    # Calculate process time (difference from Day 0 in hours)
    df["process_time_hours"] = (df["date_time"] - day_0_time).dt.total_seconds() / 3600

    # Ensure viable_cells_per_ml is numeric
    df["viable_cells_per_ml"] = pd.to_numeric(df["viable_cells_per_ml"], errors="coerce")

    # Initialize cumulative generations
    df["cumulative_generations"] = 0.0

    # Iterate over the dataframe to calculate cumulative generations
    for i in range(1, len(df)):
        df.loc[i, "cumulative_generations"] = (
                abs(np.log2(df.loc[i, "viable_cells_per_ml"] / df.loc[i - 1, "viable_cells_per_ml"]))
                + df.loc[i - 1, "cumulative_generations"]
        )

    # ✅ Calculate doubling time
    df["doubling_time"] = np.nan  # Initialize column with NaN

    for i in range(1, len(df)):
        vcd1 = df.loc[i - 1, "viable_cells_per_ml"]
        vcd2 = df.loc[i, "viable_cells_per_ml"]
        t1 = df.loc[i - 1, "process_time_hours"]
        t2 = df.loc[i, "process_time_hours"]

        if vcd1 > 0 and vcd2 > 0 and t2 > t1:
            # df.loc[i, "doubling_time"] = abs(np.log(2) * (t2 - t1)) / (np.log(vcd2) - np.log(vcd1))
            df.loc[i, "doubling_time"] = abs((np.log(2) / np.log((vcd2 / vcd1)))) / (t2 - t1)

    # df["doubling_time"] = df["process_time_hours"] / df["cumulative_generations"]

    # Handle potential NaN values (e.g., at Day 0)
    df["cumulative_generations"] = df["cumulative_generations"].fillna(0)


    # ✅ Convert datetime column to string for display
    df["date_time"] = df["date_time"].astype(str)

    #Round Calculated Values
    df["process_time_hours"] = df["process_time_hours"].round(2)
    df["cumulative_generations"] = df["cumulative_generations"].round(2)
    df["doubling_time"] = df["doubling_time"].round(2)

    # ✅ Return updated data and column headers
    return df.to_dict("records")
