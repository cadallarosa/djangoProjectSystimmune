import traceback
import os
import subprocess
import requests
from dash import html, dcc, Input, Output
from django_plotly_dash import DjangoDash
from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import \
    process_opcua_node_ids
from datetime import datetime

app = DjangoDash("ServerControlApp")

NODE_SERVER_URL = "http://django.systimmune.net:3000"

app.layout = html.Div(
    style={"fontFamily": "Arial", "padding": "20px"},
    children=[
        html.H2("Akta Data Import Server Control", style={"color": "#0056b3"}),
        html.Div(id="server-status", style={"marginBottom": "20px", "fontSize": "18px"}),

        html.Button("Check Server Status", id="check-status-btn", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Restart Server", id="restart-server-btn", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Trigger Import", id="trigger-import-btn", n_clicks=0),
        html.Button("Run OPC Import", id="run-opc-btn", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Trigger OPC Import (via Django)", id="trigger-opc-btn", n_clicks=0, style={"marginRight": "10px"}),

        html.Div(id="action-output", style={"marginTop": "30px", "fontSize": "16px", "color": "#333"}),
        dcc.Interval(id="status-refresh", interval=10000, n_intervals=0)  # Auto refresh every 10s
    ]
)


# Status check
@app.callback(
    Output("server-status", "children"),
    Input("check-status-btn", "n_clicks"),
    Input("status-refresh", "n_intervals")
)
def check_server_status(n_clicks, n_intervals):
    try:
        response = requests.get(f"{NODE_SERVER_URL}/api/serverstatus", timeout=3)
        data = response.json()
        if data.get("status") == "connected":
            return "🟢 Server is running"
        return "🔴 Server is not connected"
    except Exception:
        return "🔴 Server is not responding"


# Restart server
@app.callback(
    Output("action-output", "children"),
    Input("restart-server-btn", "n_clicks"),
    prevent_initial_call=True
)
def restart_node_server(n_clicks):
    try:
        script_path = r"C:\Users\cdallarosa\DataAlchemy\untitled\node_id_identification.js"
        node_path = "/usr/bin/node"  # Or use `which node` in your terminal

        # Optional: kill existing process if running (only if you're not using pm2/systemctl)
        os.system("pkill -f node_id_identification.js")

        # Start the server again
        subprocess.Popen([node_path, script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return "🔁 Server restart triggered."
    except Exception as e:
        return f"❌ Failed to restart server: {e}"


# Trigger import
@app.callback(
    Output("action-output", "children", allow_duplicate=True),
    Input("trigger-import-btn", "n_clicks"),
    prevent_initial_call=True
)
def trigger_import(n_clicks):
    try:
        res = requests.post(f"{NODE_SERVER_URL}/api/traverse/trigger", timeout=20)
        if res.status_code == 200:
            return "✅ Traversal/import triggered successfully."
        else:
            return f"⚠️ Server responded with: {res.status_code} - {res.text}"
    except Exception as e:
        return f"❌ Failed to trigger import: {e}"


@app.callback(
    Output("action-output", "children", allow_duplicate=True),
    Input("run-opc-btn", "n_clicks"),
    prevent_initial_call=True
)
def run_opc_import_callback(n_clicks):
    try:
        start_time = "2013-01-01T00:00:00"
        end_time = datetime.now().isoformat()
        process_opcua_node_ids(start_time, end_time)
        return "✅ OPC historical import completed successfully."
    except Exception as e:
        return f"❌ OPC Import Failed: {e}\n{traceback.format_exc()}"


@app.callback(
    Output("action-output", "children", allow_duplicate=True),
    Input("trigger-opc-btn", "n_clicks"),
    prevent_initial_call=True
)
def trigger_opc_via_django(n_clicks):
    try:
        # Replace with your actual Django host and port if needed
        response = requests.post("http://localhost:8000/api/trigger-opc-import/", timeout=30)
        data = response.json()
        if response.status_code == 200 and data.get("success"):
            return f"✅ Django OPC Import Triggered: {data.get('message')}"
        return f"⚠️ Django responded with error: {data.get('error')}"
    except Exception as e:
        return f"❌ Failed to contact Django: {e}"
