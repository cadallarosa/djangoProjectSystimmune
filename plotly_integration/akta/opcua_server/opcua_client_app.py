import dash
from dash import dcc, html, Input, Output, State, dash_table, ALL
from django_plotly_dash import DjangoDash
import pandas as pd
import plotly.graph_objs as go
from opcua import Client, ua
from datetime import datetime, timedelta
import json
import os
from dash.exceptions import PreventUpdate

# OPC UA Configuration
PKI_DIR = r"C:\Users\cdallarosa\DataAlchemy\PythonProject1\pki"
CLIENT_CERT = os.path.join(PKI_DIR, "own/certs/OWN.cer")
CLIENT_KEY = os.path.join(PKI_DIR, "own/private/uaexpert_privatekey.pem")
SERVER_CERT = os.path.join(PKI_DIR, "trusted/certs/HDAServer [84CD0A9C66CC7AA72575C3DBBDCFF83B0F84BCC1].der")
SERVER_URL = "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer"
CUSTOM_ROOT_PATH = "ns=2;s=2:Archive/OPCuser/Folders"

# Initialize the Dash app
app = DjangoDash("OPCBrowserApp", suppress_callback_exceptions=True)


# ====================== OPC UA Helper Functions ======================
def get_opc_client():
    """Create and configure an OPC UA client with security settings"""
    client = Client(SERVER_URL)
    client.application_uri = "urn:SI-CF8MJX3:UnifiedAutomation:UaExpert"
    client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{CLIENT_CERT},{CLIENT_KEY},{SERVER_CERT}")
    client.set_user("OPCuser")
    client.set_password("OPCuser_710l")
    client.session_timeout = 30000
    client.uaclient.timeout = 30000
    return client


def browse_node(node):
    """Get children of a node with error handling"""
    try:
        return node.get_children()
    except Exception as e:
        print(f"Error browsing node: {e}")
        return []


def read_historical_data(node, start_time=None, end_time=None, days=1):
    """Read historical data from a node with time range"""
    if start_time is None or end_time is None:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

    try:
        history = node.read_raw_history(starttime=start_time, endtime=end_time)
        return [(entry.SourceTimestamp, entry.Value.Value, entry.StatusCode.name)
                for entry in history if entry.Value.Value is not None]
    except Exception as e:
        print(f"Error reading history: {e}")
        return []


def get_custom_root_node(client):
    """Navigate to the custom starting node path"""
    try:
        path_components = CUSTOM_ROOT_PATH.split('/')
        current_node = client.get_node(path_components[0])

        for component in path_components[1:]:
            current_node = current_node.get_child(["2:" + component])

        return current_node
    except Exception as e:
        print(f"Error navigating to custom root: {e}")
        return None


# ====================== UI Helper Functions ======================
def get_default_time_range(days=1):
    """Get default time range for historical data"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    return start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S')


def is_endpoint_node(node):
    """Check if a node is an endpoint (has a value)"""
    try:
        node.get_value()
        return True
    except:
        return False


def render_tree(node, client, level=0, expanded_nodes=None):
    """Recursively render the OPC UA node tree"""
    if expanded_nodes is None:
        expanded_nodes = set()

    children = browse_node(node)
    items = []
    for child in children:
        try:
            name = child.get_browse_name().Name
            node_id = child.nodeid.to_string()
            node_class = child.get_node_class()
            is_folder = node_class == ua.NodeClass.Object
            is_endpoint = is_endpoint_node(child) if not is_folder else False

            # Create expand/collapse button for folders
            if is_folder:
                expanded = node_id in expanded_nodes
                button = html.Span(
                    "▶" if not expanded else "▼",
                    style={"cursor": "pointer", "marginRight": "5px"}
                )
            else:
                button = html.Span(" ", style={"marginRight": "15px"})

            # Different icons for different node types
            icon = "📁" if is_folder else ("🔌" if is_endpoint else "📄")

            label = html.Div(
                [button, html.Span(f"{icon} {name}")],
                id={'type': 'opc-node', 'node_id': node_id},
                n_clicks=0,
                style={
                    "marginLeft": f"{level * 10}px",
                    "cursor": "pointer",
                    "padding": "3px",
                    "userSelect": "none",
                    "borderBottom": "1px solid #eee",
                    "backgroundColor": "#fff" if level % 2 == 0 else "#f9f9f9"
                }
            )
            items.append(label)

            # Recursively add children if expanded
            if is_folder and node_id in expanded_nodes:
                items.extend(render_tree(child, client, level + 1, expanded_nodes))

        except Exception as e:
            print(f"Error rendering node {child}: {e}")
            continue

    if not items:
        items.append(html.Div("(Empty)", style={
            "marginLeft": f"{level * 10}px",
            "color": "#888",
            "fontStyle": "italic"
        }))
    return items


# ====================== App Layout ======================
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='dummy-output', style={'display': 'none'}),

    html.H2("OPC UA Browser", style={'marginBottom': '20px'}),

    # Connection status bar
    html.Div(id='connection-status', style={
        'padding': '10px',
        'marginBottom': '20px',
        'borderRadius': '5px',
        'fontWeight': 'bold'
    }),

    # Main content area
    html.Div([
        # Tree view panel
        html.Div([
            html.Div([
                html.Label("OPC UA Node Tree", style={'fontWeight': 'bold'}),
                html.Button("Refresh", id='refresh-tree-btn', style={'float': 'right', 'marginLeft': '10px'}),
                html.Button("Collapse All", id='collapse-all-btn', style={'float': 'right'})
            ], style={'marginBottom': '10px'}),
            html.Div(id="opc-tree", style={
                "width": "100%",
                "overflowY": "auto",
                "height": "500px",
                "border": "1px solid #ddd",
                "padding": "10px",
                "backgroundColor": "#f9f9f9"
            })
        ], style={"width": "30%", "paddingRight": "15px"}),

        # Details panel
        html.Div([
            html.Div([
                html.H4("Node Information", style={'marginTop': '0'}),
                html.Div(id="node-info", style={
                    'padding': '15px',
                    'border': '1px solid #ddd',
                    'borderRadius': '5px',
                    'marginBottom': '20px',
                    'backgroundColor': '#fff'
                }),

                html.H4("Historical Data"),
                html.Div([
                    html.Label("Start Time:"),
                    dcc.Input(
                        id='start-time',
                        type='text',
                        placeholder='YYYY-MM-DD HH:MM:SS',
                        style={'marginRight': '10px'}
                    ),
                    html.Label("End Time:"),
                    dcc.Input(
                        id='end-time',
                        type='text',
                        placeholder='YYYY-MM-DD HH:MM:SS',
                        style={'marginRight': '10px'}
                    ),
                    html.Button("Read Data", id="read-data-btn", style={'marginRight': '10px'}),
                    html.Button("Download CSV", id="btn-csv"),
                ], style={'marginBottom': '15px'}),

                html.Div(id="data-preview", style={
                    'border': '1px solid #ddd',
                    'borderRadius': '5px',
                    'padding': '15px',
                    'minHeight': '300px',
                    'backgroundColor': '#fff'
                }),

                dcc.Download(id="download-data"),
                dcc.Store(id="selected-node-id"),
                dcc.Store(id="expanded-nodes", data=[]),
                dcc.Store(id='tree-data')
            ], style={"width": "100%"})
        ], style={"width": "70%", "paddingLeft": "15px"})
    ], style={"display": "flex", "gap": "20px"})
])


# ====================== Callbacks ======================
@app.callback(
    Output("connection-status", "children"),
    Output("connection-status", "style"),
    Input("url", "pathname")
)
def update_connection_status(_):
    try:
        client = get_opc_client()
        client.connect()

        try:
            root = client.get_root_node()
            server_node = root.get_child(["0:Objects", "0:Server"])
            server_name = server_node.get_child("0:ServerArray").get_value()[0]
            status_text = f"✔ Connected to OPC UA Server: {server_name}"
        except:
            status_text = "✔ Connected to OPC UA Server"

        client.disconnect()
        return status_text, {'backgroundColor': '#d4edda', 'color': '#155724'}
    except Exception as e:
        return f"✖ Connection Error: {str(e)}", {'backgroundColor': '#f8d7da', 'color': '#721c24'}


@app.callback(
    Output("opc-tree", "children"),
    Output("tree-data", "data"),
    Input("refresh-tree-btn", "n_clicks"),
    Input("collapse-all-btn", "n_clicks"),
    State("expanded-nodes", "data")
)
def update_tree(refresh_clicks, collapse_clicks, expanded_nodes):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if trigger_id == 'collapse-all-btn':
        return [], []

    try:
        client = get_opc_client()
        client.connect()
        root = get_custom_root_node(client)

        if not root:
            return [html.Div("Error: Custom root path not found", style={"color": "red"})], None

        tree = render_tree(root, client, 0, set(expanded_nodes or []))
        client.disconnect()

        return tree, {'root_id': root.nodeid.to_string()}
    except Exception as e:
        return [html.Div(f"Error loading tree: {str(e)}", style={"color": "red"})], None


@app.callback(
    Output("selected-node-id", "data"),
    Input({'type': 'opc-node', 'node_id': ALL}, 'n_clicks'),
    State({'type': 'opc-node', 'node_id': ALL}, 'id')
)
def store_selected_node(clicks, ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    clicked_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
    return clicked_id['node_id']


@app.callback(
    Output("expanded-nodes", "data"),
    Input({'type': 'opc-node', 'node_id': ALL}, 'n_clicks'),
    State({'type': 'opc-node', 'node_id': ALL}, 'id'),
    State("expanded-nodes", "data")
)
def toggle_node_expansion(clicks, ids, expanded_nodes):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    clicked_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
    node_id = clicked_id['node_id']

    expanded_nodes = expanded_nodes or []
    expanded_nodes.remove(node_id) if node_id in expanded_nodes else expanded_nodes.append(node_id)
    return expanded_nodes


@app.callback(
    Output("node-info", "children"),
    Input("selected-node-id", "data"),
    prevent_initial_call=True
)
def show_node_info(node_id):
    if not node_id:
        return "Select a node to view its information."

    try:
        client = get_opc_client()
        client.connect()
        node = client.get_node(node_id)

        info = {
            'Name': node.get_browse_name().Name,
            'Node ID': node_id,
            'Node Class': str(node.get_node_class()).split('.')[-1],
            'Data Type': getattr(node.get_data_type(), 'to_string', lambda: "N/A")(),
            'Value': getattr(node, 'get_value', lambda: "N/A")(),
            'Access Level': getattr(node, 'get_access_level', lambda: "N/A")(),
            'Historizing': getattr(node.get_attribute(ua.AttributeIds.Historizing).Value, 'Value', "N/A"),
            'Description': getattr(node.get_description(), 'Text', "N/A")
        }

        client.disconnect()

        return html.Div([
            html.Table([html.Tr([html.Td(k + ":"), html.Td(str(v))]) for k, v in info.items()],
                       style={'width': '100%'})
        ])
    except Exception as e:
        return html.Div(f"Error reading node info: {str(e)}", style={"color": "red"})


@app.callback(
    Output("data-preview", "children"),
    Output("download-data", "data"),
    Input("read-data-btn", "n_clicks"),
    State("selected-node-id", "data"),
    State("start-time", "value"),
    State("end-time", "value"),
    prevent_initial_call=True
)
def read_data(n_clicks, node_id, start_time, end_time):
    if not node_id:
        return html.Div("Please select a node first", style={"color": "red"}), None

    if not start_time or not end_time:
        default_start, default_end = get_default_time_range()
        return html.Div([
            html.P("Using default time range (last 24 hours)", style={"color": "gray"}),
            html.P(f"Start: {default_start}"),
            html.P(f"End: {default_end}"),
            html.Button("Read Data with Default Range", id="read-default-btn")
        ]), None

    try:
        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        client = get_opc_client()
        client.connect()
        node = client.get_node(node_id)

        try:
            if not node.get_attribute(ua.AttributeIds.Historizing).Value.Value:
                return "Node is not configured for historizing", None
        except:
            return "Historizing not supported for this node", None

        history = read_historical_data(node, start_dt, end_dt)
        client.disconnect()

        if not history:
            return "No historical data available", None

        df = pd.DataFrame(history, columns=["Timestamp", "Value", "Status"])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])

        fig = go.Figure(data=[go.Scatter(
            x=df['Timestamp'], y=df['Value'], mode='lines+markers'
        )])
        fig.update_layout(
            title=f"Historical Data for {node.get_browse_name().Name}",
            xaxis_title="Time", yaxis_title="Value"
        )

        table = dash_table.DataTable(
            id='history-table',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            page_size=10,
            style_table={'overflowX': 'auto'}
        )

        return html.Div([
            dcc.Graph(figure=fig),
            html.H5("Raw Data", style={'marginTop': '20px'}),
            table
        ]), dcc.send_data_frame(df.to_csv, filename=f"opc_data_{node_id.replace(':', '_')}.csv")

    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD HH:MM:SS", None
    except Exception as e:
        return f"Error reading data: {str(e)}", None


# Initial tree load
@app.callback(
    Output("opc-tree", "children", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call=True
)
def load_tree(_):
    try:
        client = get_opc_client()
        client.connect()
        root = get_custom_root_node(client)
        tree = render_tree(root, client) if root else [html.Div("Custom root path not found", style={"color": "red"})]
        client.disconnect()
        return tree
    except Exception as e:
        return [html.Div(f"Error loading tree: {str(e)}", style={"color": "red"})]