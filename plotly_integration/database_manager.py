import os
from dash import dcc, html
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash
from django.conf import settings
import plotly_integration.database.process_ars as process_ars
import plotly_integration.database.process_arw as process_arw

# Get database name from settings
DB_NAME = settings.DATABASES['default']['NAME']

# Initialize the Dash app
app = DjangoDash('DatabaseManagerApp')

# Define the layout with active file monitoring
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f8f9fa",
        "padding": "20px",
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "center",
        "alignItems": "center",
    },
    children=[
        html.Div(
            style={
                "width": "70%",
                "backgroundColor": "white",
                "borderRadius": "10px",
                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
                "padding": "40px",
                "textAlign": "center",
            },
            children=[
                html.H1(
                    "Database Management Tool",
                    style={
                        "color": "#333",
                        "marginBottom": "30px",
                        "fontSize": "32px",
                    },
                ),
                html.Div(
                    style={"marginBottom": "30px"},
                    children=[
                        html.Label(
                            "Select Folder Containing Raw Files",
                            style={"fontSize": "20px", "marginBottom": "10px", "display": "block"},
                        ),
                        dcc.Input(
                            id="folder-path",
                            type="text",
                            value="S:\\Shared\\Chris Dallarosa\\Database Imports",
                            style={
                                "width": "100%",
                                "padding": "15px",
                                "border": "1px solid #ccc",
                                "borderRadius": "5px",
                                "fontSize": "18px",
                            },
                        ),
                    ],
                ),
                html.Div(
                    id="file-count-message",
                    style={
                        "marginBottom": "30px",
                        "fontSize": "18px",
                        "color": "#555",
                    },
                ),
                html.Div(
                    style={"marginBottom": "30px"},
                    children=[
                        html.Label(
                            "Select Reported Folder",
                            style={"fontSize": "20px", "marginBottom": "10px", "display": "block"},
                        ),
                        dcc.Input(
                            id="reported-folder",
                            type="text",
                            value="S:\\Shared\\Chris Dallarosa\\Database Imported",
                            style={
                                "width": "100%",
                                "padding": "15px",
                                "border": "1px solid #ccc",
                                "borderRadius": "5px",
                                "fontSize": "18px",
                            },
                        ),
                    ],
                ),
                html.Button(
                    "Start Import",
                    id="start-import-btn",
                    style={
                        "backgroundColor": "#007bff",
                        "color": "white",
                        "padding": "15px 30px",
                        "border": "none",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "18px",
                    },
                ),
                html.Div(
                    id="output-message",
                    style={
                        "marginTop": "30px",
                        "fontSize": "18px",
                        "color": "#333",
                    },
                ),
                # Interval component for active monitoring
                dcc.Interval(
                    id="interval-component",
                    interval=5000,  # Check every 5 seconds
                    n_intervals=0,  # Number of intervals passed
                ),
            ],
        ),
    ],
)

# Callback to monitor folder and update file count
@app.callback(
    Output("file-count-message", "children"),
    [Input("interval-component", "n_intervals")],
    [State("folder-path", "value")],
)
def monitor_folder(n_intervals, folder_path):
    if not folder_path or not os.path.isdir(folder_path):
        return "Invalid folder path. Please select a valid folder."

    # Count the number of `.ars` and `.arw` files
    ars_files = len([f for f in os.listdir(folder_path) if f.endswith(".ars")])
    arw_files = len([f for f in os.listdir(folder_path) if f.endswith(".arw")])
    total_files = ars_files + arw_files

    if total_files == 0:
        return "No files found in the selected folder."
    return f"Folder contains {total_files} file(s): {ars_files} .ars file(s) and {arw_files} .arw file(s)."

# Callback for processing files
@app.callback(
    Output("output-message", "children"),
    [Input("start-import-btn", "n_clicks")],
    [State("folder-path", "value"), State("reported-folder", "value")]
)
def start_import(n_clicks, folder_path, reported_folder):
    if not n_clicks or n_clicks == 0:
        return "Click 'Start Import' to begin."

    # Validate inputs
    if not os.path.isdir(folder_path):
        return f"Error: Folder '{folder_path}' does not exist."
    if not os.path.isdir(reported_folder):
        return f"Error: Reported folder '{reported_folder}' does not exist."
    if not os.path.isfile(DB_NAME):
        return f"Error: Database file '{DB_NAME}' does not exist."

    try:
        # Process files
        ars_files = [f for f in os.listdir(folder_path) if f.endswith(".ars")]
        arw_files = [f for f in os.listdir(folder_path) if f.endswith(".arw")]

        # Process .ars files
        for file in ars_files:
            process_ars.process_files(directory=folder_path, reported_folder=reported_folder, db_name=DB_NAME)

        # Process .arw files
        for file in arw_files:
            process_arw.process_files(directory=folder_path, reported_folder=reported_folder, db_name=DB_NAME)

        return "File import completed successfully!"
    except Exception as e:
        return f"An error occurred: {str(e)}"
