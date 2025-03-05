from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
import base64
import io

from plotly_integration.models import UFDFMetadata, SartoflowTimeSeriesData

# Initialize the Dash app
app = DjangoDash("UFDFAnalysis")

# Available options
molecule_options = [{"label": "SI-50E15", "value": "SI-50E15"}]
cassette_options = [
    {"label": "Cassette A", "value": "cassette_a"},
    {"label": "Cassette B", "value": "cassette_b"},
    {"label": "Cassette C", "value": "cassette_c"},
]

# Define layout
app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "padding": "20px"},
    children=[
        dcc.Tabs(
            id="tabs",
            value="ufdf",
            children=[
                dcc.Tab(label="UFDF", value="ufdf", style={"fontSize": "18px"}),
                dcc.Tab(label="Viral Filtration", value="viral", style={"fontSize": "18px"}),
            ],
            colors={"border": "white", "primary": "darkblue", "background": "white"},
        ),
        html.Div(id="tab-content"),
    ],
)

# UFDF Tab Layout
ufdf_layout = html.Div(
    style={"maxWidth": "800px", "margin": "0 auto"},  # Centers content and limits width
    children=[
        html.H2("UFDF Experiment Analysis", style={"textAlign": "center", "color": "#0047b3", "marginBottom": "20px"}),

        # Molecule selection
        html.Label("Select Molecule:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Dropdown(id="molecule-select", options=molecule_options, placeholder="Choose a molecule",
                     style={"marginBottom": "15px"}),

        # Experiment Name
        html.Label("Experiment Name:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Input(id="experiment-name", type="text", placeholder="Enter experiment name",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        # Experimental Notes
        html.Label("Experimental Notes:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Textarea(id="experiment-notes", placeholder="Enter experimental details...",
                     style={"width": "100%", "height": "100px", "padding": "10px", "marginBottom": "20px"}),

        # Cassette selection
        html.Label("Select Cassette Type:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Dropdown(id="cassette-select", options=cassette_options, placeholder="Choose a cassette",
                     style={"marginBottom": "15px"}),

        # Load inputs
        html.Label("Load Concentration (mg/mL):", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Input(id="load-concentration", type="number", placeholder="Enter load concentration",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Load Volume (mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="load-volume", type="number", placeholder="Enter load volume",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Load Mass (mg):", style={"fontWeight": "bold"}),
        html.Div(id="load-mass", style={"fontSize": "18px", "fontWeight": "bold", "marginBottom": "15px"}),

        # Process Inputs
        html.Label("UF1 Target Reservoir Mass (g):", style={"fontWeight": "bold"}),
        dcc.Input(id="uf1-mass", type="number", placeholder="Enter UF1 target mass",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("#Diavolumes:", style={"fontWeight": "bold"}),
        dcc.Input(id="diavolumes", type="number", placeholder="Enter number of diavolumes",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Permeate Target Mass (g):", style={"fontWeight": "bold"}),
        dcc.Input(id="permeate-mass", type="number", placeholder="Enter permeate target mass",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Diafiltration Volume Required (mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="diafiltration-volume", type="number", placeholder="Enter diafiltration volume",
                  style={"width": "100%", "padding": "10px", "marginBottom": "20px"}),

        html.H3("Filtration Settings", style={"marginTop": "20px", "color": "#0047b3"}),

        html.Label("LMH Target:", style={"fontWeight": "bold"}),
        dcc.Input(id="lmh-target", type="number", placeholder="Enter LMH target",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Flow Rate (mL/min):", style={"fontWeight": "bold"}),
        dcc.Input(id="flow-rate", type="number", placeholder="Enter flow rate",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Target Flow Rate (mL/min):", style={"fontWeight": "bold"}),
        dcc.Input(id="target-flow-rate", type="number", placeholder="Enter target flow rate",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Target P2500 Setpoint (%):", style={"fontWeight": "bold"}),
        dcc.Input(id="p2500-setpoint", type="number", placeholder="Enter P2500 setpoint",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Target P3000 Setpoint:", style={"fontWeight": "bold"}),
        dcc.Input(id="p3000-setpoint", type="number", placeholder="Enter P3000 setpoint",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.H3("Final Results", style={"marginTop": "20px", "color": "#0047b3"}),

        html.Label("Final Volume (mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="final-volume", type="number", placeholder="Enter final volume",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Final Concentration (mg/mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="final-concentration", type="number", placeholder="Enter final concentration",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Product Mass (mg):", style={"fontWeight": "bold"}),
        dcc.Input(id="product-mass", type="number", placeholder="Enter product mass",
                  style={"width": "100%", "padding": "10px", "marginBottom": "15px"}),

        html.Label("Yield (%):", style={"fontWeight": "bold"}),
        dcc.Input(id="yield", type="number", placeholder="Enter yield",
                  style={"width": "100%", "padding": "10px", "marginBottom": "20px"}),

        html.H3("Upload Data File", style={"marginTop": "20px", "color": "#0047b3"}),

        dcc.Upload(
            id="upload-data",
            children=html.Button("Upload File", style={"backgroundColor": "#0047b3", "color": "white", "border": "none",
                                                       "padding": "10px 20px", "cursor": "pointer"}),
            multiple=False,
            style={"marginBottom": "20px"},
        ),
        html.Div(id="upload-status", style={"marginTop": "10px", "color": "green"}),

        # Data Table Preview
        html.H3("Uploaded Data Preview", style={"marginTop": "20px", "color": "#0047b3"}),
        dash_table.DataTable(
            id="data-preview",
            columns=[],
            data=[],
            style_table={"overflowX": "auto", "marginTop": "10px"},
            style_cell={"textAlign": "center", "padding": "5px"},
            style_header={"fontWeight": "bold", "backgroundColor": "#e9f1fb"},
        ),
        html.Button("Import and Submit Report", id="submit-report", n_clicks=0,
                    style={"backgroundColor": "#28a745", "color": "white", "padding": "10px 20px",
                           "marginTop": "20px"}),

        html.Div(id="final-status", style={"marginTop": "10px", "color": "blue"}),

    ]
)


@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
)
def render_tab_content(tab):
    if tab == "ufdf":
        return ufdf_layout
    else:
        return html.Div(html.H3("Viral Filtration Analysis (Coming Soon)", style={"textAlign": "center"}))


@app.callback(
    Output("load-mass", "children"),
    [Input("load-concentration", "value"), Input("load-volume", "value")],
)
def calculate_load_mass(concentration, volume):
    if concentration and volume:
        return f"{concentration * volume:.2f} mg"
    return "N/A"


# Define a function to parse CSV file
def parse_csv(contents):
    """
    Parses uploaded CSV file, assigns correct headers, and returns a DataFrame.
    """
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    try:
        # Read CSV, skipping first 4 rows (since data starts on row 5)
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8-sig")), delimiter=";", skiprows=4, header=None)

        # Define correct headers (36 headers for 36 columns)
        correct_headers = [
            "BatchId", "PDatTime", "ProcessTime",
            "AG2100_Value", "AG2100_Setpoint", "AG2100_Mode", "AG2100_Output",
            "DPRESS_Value", "DPRESS_Output", "DPRESS_Mode", "DPRESS_Setpoint",
            "F_PERM_Value",
            "P2500_Setpoint", "P2500_Value", "P2500_Output", "P2500_Mode",
            "P3000_Setpoint", "P3000_Mode", "P3000_Output", "P3000_Value", "P3000_T",
            "PIR2600", "PIR2700",
            "PIRC2500_Output", "PIRC2500_Value", "PIRC2500_Setpoint", "PIRC2500_Mode",
            "QIR2000", "QIR2100",
            "TIR2100", "TMP",
            "WIR2700",
            "WIRC2100_Value", "WIRC2100_Output", "WIRC2100_Setpoint", "WIRC2100_Mode"
        ]

        # Ensure correct number of columns before assigning headers
        if len(df.columns) != len(correct_headers):
            raise ValueError(f"Column mismatch! Expected {len(correct_headers)} columns, but found {len(df.columns)}.")

        # Assign correct headers
        df.columns = correct_headers

        # Convert PDatTime to datetime format
        df["PDatTime"] = pd.to_datetime(df["PDatTime"], errors="coerce")

        # Drop rows where `BatchId` is NaN
        df = df.dropna(subset=["BatchId"])

        # Ensure `BatchId` is always a string and non-null
        df["BatchId"] = df["BatchId"].astype(str).str.strip()

        # Remove completely empty rows
        df = df.dropna(how="all")

        # Replace NaN values with None for database insertion
        df = df.where(pd.notnull(df), None)

        return df
    except Exception as e:
        return str(e)  # Return error message as string


@app.callback(
    [Output("upload-status", "children"), Output("data-preview", "columns"), Output("data-preview", "data")],
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True
)
def upload_file(contents, filename):
    if contents is None:
        return "Upload failed.", [], []

    # Parse CSV file once
    df = parse_csv(contents)

    if isinstance(df, str):  # If parsing returned an error message
        return f"Error parsing file: {df}", [], []

    # Prepare data for preview
    data = df.head(10).to_dict("records")
    return f"File '{filename}' successfully uploaded!", [{"name": col, "id": col} for col in df.columns], data


@app.callback(
    Output("final-status", "children"),
    Input("submit-report", "n_clicks"),
    State("upload-data", "contents"),
    State("molecule-select", "value"),
    State("experiment-name", "value"),
    State("experiment-notes", "value"),
    State("cassette-select", "value"),
    State("load-concentration", "value"),
    State("load-volume", "value"),
    prevent_initial_call=True
)
def handle_import(n_clicks, contents, molecule_name, experiment_name, experiment_notes,
                  cassette_type, load_concentration, load_volume):
    if not contents:
        return "Upload failed."

    # Parse CSV file once
    df = parse_csv(contents)

    if isinstance(df, str):  # If parsing returned an error message
        return f"Error parsing file: {df}"

    # Step 1: Create UFDFMetadata entry
    ufdf_metadata = UFDFMetadata.objects.create(
        molecule_name=molecule_name,
        experiment_name=experiment_name,
        experimental_notes=experiment_notes,
        cassette_type=cassette_type,
        load_concentration=load_concentration,
        load_volume=load_volume,
        load_mass=(load_concentration * load_volume) if load_concentration and load_volume else None,
    )

    # Step 2: Insert Sartoflow data with result_id
    time_series_records = []
    for _, row in df.iterrows():
        time_series_records.append(SartoflowTimeSeriesData(
            result_id=ufdf_metadata,
            batch_id=row.get('BatchId'),
            pdat_time=pd.to_datetime(row.get('PDatTime'), errors='coerce'),  # Convert to datetime
            process_time=row.get('ProcessTime', 0),
            ag2100_value=row.get('AG2100_Value'),
            ag2100_setpoint=row.get('AG2100_Setpoint'),
            ag2100_mode=row.get('AG2100_Mode'),
            ag2100_output=row.get('AG2100_Output'),
            dpress_value=row.get('DPRESS_Value'),
            dpress_output=row.get('DPRESS_Output'),
            dpress_mode=row.get('DPRESS_Mode'),
            dpress_setpoint=row.get('DPRESS_Setpoint'),
            f_perm_value=row.get('F_PERM_Value'),
            p2500_setpoint=row.get('P2500_Setpoint'),
            p2500_value=row.get('P2500_Value'),
            p2500_output=row.get('P2500_Output'),
            p2500_mode=row.get('P2500_Mode'),
            p3000_setpoint=row.get('P3000_Setpoint'),
            p3000_mode=row.get('P3000_Mode'),
            p3000_output=row.get('P3000_Output'),
            p3000_value=row.get('P3000_Value'),
            p3000_t=row.get('P3000_T'),
            pir2600=row.get('PIR2600'),
            pir2700=row.get('PIR2700'),
            pirc2500_value=row.get('PIRC2500_Value'),
            pirc2500_output=row.get('PIRC2500_Output'),
            pirc2500_setpoint=row.get('PIRC2500_Setpoint'),
            pirc2500_mode=row.get('PIRC2500_Mode'),
            qir2000=row.get('QIR2000'),
            qir2100=row.get('QIR2100'),
            tir2100=row.get('TIR2100'),
            tmp=row.get('TMP'),
            wir2700=row.get('WIR2700'),
            wirc2100_output=row.get('WIRC2100_Output'),
            wirc2100_setpoint=row.get('WIRC2100_Setpoint'),
            wirc2100_mode=row.get('WIRC2100_Mode'),
        ))

    SartoflowTimeSeriesData.objects.bulk_create(time_series_records)

    return f"Successfully imported {len(time_series_records)} records for Result ID {ufdf_metadata.result_id}"
