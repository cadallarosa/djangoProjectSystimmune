import os
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash
from .process_asc import save_asc_to_db, move_file_to_processed

# Initialize the Dash app
app = DjangoDash('CeSdsImportManagerApp', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = html.Div([
    html.H2("CE SDS Import Manager", style={"textAlign": "center", "marginBottom": "20px"}),

    html.Div([
        html.Label("Incoming Folder (.asc files):"),
        dcc.Input(id="incoming-folder", type="text", value="S:\\Shared\\Chris Dallarosa\\CE_SDS", style={"width": "100%"}),

        html.Label("Processed Folder (move after import):", style={"marginTop": "15px"}),
        dcc.Input(id="processed-folder", type="text", value="S:\\Shared\\Chris Dallarosa\\CE SDS Imported", style={"width": "100%"}),

        html.Div([
            html.Button("Start Import", id="start-import-btn", style={
                "marginTop": "20px", "marginBottom": "10px",
                "backgroundColor": "#007bff", "color": "white",
                "padding": "10px 30px", "border": "none",
                "borderRadius": "5px", "cursor": "pointer", "fontSize": "16px"
            }),
            html.Button("Cancel Import", id="cancel-import-btn", style={
                "marginTop": "20px", "marginBottom": "10px", "marginLeft": "10px",
                "backgroundColor": "#dc3545", "color": "white",
                "padding": "10px 30px", "border": "none",
                "borderRadius": "5px", "cursor": "poianter", "fontSize": "16px"
            })
        ], style={"textAlign": "center"})
    ], style={"width": "60%", "margin": "auto"}),

    html.Hr(),

    dcc.Store(id="import-status-store"),
    dcc.Interval(id="progress-interval", interval=500, n_intervals=0, disabled=True),

    html.Div(id="current-filename", style={"textAlign": "center", "fontSize": "18px", "marginBottom": "10px"}),
    dbc.Progress(id="progress-bar", value=0, label="0%", striped=True, animated=True, style={"height": "30px", "margin": "0 20%"}),

    html.Div(id="final-message", style={"textAlign": "center", "fontSize": "20px", "marginTop": "20px", "color": "green"})
])

# Combined Callback for Start, Progress, Cancel and Interval Control
@app.callback(
    [Output("import-status-store", "data"),
     Output("progress-interval", "disabled")],
    [Input("start-import-btn", "n_clicks"),
     Input("progress-interval", "n_intervals"),
     Input("cancel-import-btn", "n_clicks")],
    [State("import-status-store", "data"),
     State("incoming-folder", "value"),
     State("processed-folder", "value")]
)
def handle_import(start_clicks, n_intervals, cancel_clicks, status, incoming_folder, processed_folder):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # --- Start Import ---
    if triggered_id == "start-import-btn":
        print("✅ Incoming folder exists:", os.path.isdir(incoming_folder))
        print("✅ Processed folder exists:", os.path.isdir(processed_folder))
        print("📁 ASC Files:", os.listdir(incoming_folder) if os.path.isdir(incoming_folder) else "Folder not found")

        if not os.path.isdir(incoming_folder) or not os.path.isdir(processed_folder):
            return {
                "progress": 0,
                "label": "0%",
                "filename": "",
                "final_message": "❌ Invalid folder paths.",
                "cancelled": False
            }, True

        processed_files = set(os.listdir(processed_folder))

        asc_files = [
            f for f in os.listdir(incoming_folder)
            if f.lower().endswith(".asc")
               and "dat-pda - 220nm" not in f.lower()
               and f not in processed_files
        ]

        if not asc_files:
            return {
                "progress": 0,
                "label": "0%",
                "filename": "",
                "final_message": "⚠️ No .asc files found to import.",
                "cancelled": False
            }, True

        return {
            "pending_files": asc_files,
            "current_index": 0,
            "total": len(asc_files),
            "progress": 0,
            "label": "0%",
            "filename": "",
            "final_message": "",
            "cancelled": False,
            "incoming_folder": incoming_folder,
            "processed_folder": processed_folder
        }, False

    # --- Cancel Import ---
    if triggered_id == "cancel-import-btn":
        if status:
            status["cancelled"] = True
            status["final_message"] = "⛔ Import Cancelled."
        return status, True  # stop interval

    # --- Progress Tick ---
    if triggered_id == "progress-interval":
        if not status:
            return dash.no_update, dash.no_update

        if status.get("cancelled", False):
            return status, True

        idx = status["current_index"]
        total = status["total"]
        pending = status["pending_files"]
        incoming_folder = status["incoming_folder"]
        processed_folder = status["processed_folder"]

        if idx >= total:
            status.update({
                "progress": 100,
                "label": "100%",
                "filename": "",
                "final_message": f"✅ Imported {total} files successfully."
            })
            return status, True

        filename = pending[idx]
        file_path = os.path.join(incoming_folder, filename)

        try:
            save_asc_to_db(file_path)
            move_file_to_processed(file_path, processed_folder)
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            return status, False  # Do not advance if failure
        else:
            # Advance only after both import and move succeed
            status["current_index"] = idx + 1
            progress = int(((idx + 1) / total) * 100)

            status.update({
                "progress": progress,
                "label": f"{progress}%",
                "filename": f"Importing: {filename}",
                "final_message": ""
            })
            return status, False  # Keep ticking

    return dash.no_update, dash.no_update


# UI Update Callback
@app.callback(
    [Output("progress-bar", "value"),
     Output("progress-bar", "label"),
     Output("current-filename", "children"),
     Output("final-message", "children")],
    Input("import-status-store", "data"),
    prevent_initial_call=True
)
def update_ui(status):
    if not status:
        return 0, "0%", "", ""

    return (
        status.get("progress", 0),
        status.get("label", "0%"),
        status.get("filename", ""),
        status.get("final_message", "")
    )
