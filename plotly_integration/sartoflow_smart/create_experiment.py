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
    {"label": "Sartocon 30kD 0.02 m^2", "value": "0.02"},
]
# Define common input box styles
input_style = {
    "width": "100%",  # Ensure all inputs have full width
    "padding": "10px",  # Consistent padding inside input boxes
    "marginBottom": "15px",  # Same spacing between inputs
    "borderRadius": "5px",  # Slight rounded corners for aesthetics
    "border": "1px solid #ccc"  # Subtle border for all inputs
}

# Define read-only input style (calculated values)
readonly_input_style = input_style.copy()
readonly_input_style["backgroundColor"] = "#e9f1fb"  # Light blue background for calculated fields
readonly_input_style["border"] = "1px solid #bbb"  # Slightly darker border for contrast

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
            colors={"border": "white", "primary": "darkblue", "background": "light-gray"},
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
                     style=input_style),

        # Experiment Name
        html.Label("Experiment Name:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Input(id="experiment-name", type="text", placeholder="Enter experiment name",
                  style=input_style),

        # Experimental Notes
        html.Label("Experimental Notes:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Textarea(id="experiment-notes", placeholder="Enter experimental details...",
                     style={"width": "100%", "height": "100px", "padding": "10px", "marginBottom": "20px"}),

        # Cassette selection
        html.Label("Select Cassette Type:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Dropdown(id="cassette-select", options=cassette_options, placeholder="Choose a cassette",
                     style=input_style),

        # Load inputs
        html.Label("Load Concentration (mg/mL):", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Input(id="load-concentration", type="number", placeholder="Enter load concentration",
                  style=input_style),

        html.Label("Load Volume (mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="load-volume", type="number", placeholder="Enter load volume",
                  style=input_style),

        html.Label("Load Mass (mg):", style={"fontWeight": "bold"}),
        dcc.Input(id="load-mass", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("UF1 Target Concentration:", style={"fontWeight": "bold"}),
        dcc.Input(id="uf1-target-concentration", type="number", placeholder="Enter load volume",
                  style=input_style),

        # Process Inputs
        html.Label("UF1 Target Reservoir Mass (g):"),
        dcc.Input(id="uf1-mass", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("#Diavolumes:", style={"fontWeight": "bold"}),
        dcc.Input(id="diavolumes", type="number", placeholder="Enter number of diavolumes",
                  style=input_style),

        html.Label("Permeate Target Mass (g):", style={"fontWeight": "bold"}),
        dcc.Input(id="permeate-mass", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        #
        html.H3("Filtration Settings", style={"marginTop": "20px", "color": "#0047b3"}),

        html.Label("LMH Target:", style={"fontWeight": "bold"}),
        dcc.Input(id="lmh-target", type="number", placeholder="Enter LMH target",
                  style=input_style),

        html.Label("Target Flow Rate (mL/min):", style={"fontWeight": "bold"}),
        dcc.Input(id="target-flow-rate", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("Target P2500 Setpoint (%):", style={"fontWeight": "bold"}),
        dcc.Input(id="p2500-setpoint", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("Target P3000 Setpoint:", style={"fontWeight": "bold"}),
        dcc.Input(id="p3000-setpoint", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.H3("Final Results", style={"marginTop": "20px", "color": "#0047b3"}),

        html.Label("Final Volume (mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="final-volume", type="number", placeholder="Enter final volume",
                  style=input_style),

        html.Label("Final Concentration (mg/mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="final-concentration", type="number", placeholder="Enter final concentration",
                  style=input_style),

        html.Label("Product Mass (mg):", style={"fontWeight": "bold"}),
        dcc.Input(id="product-mass", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("Yield (%):", style={"fontWeight": "bold"}),
        dcc.Input(id="yield", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

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


# Callbacks

@app.callback(
    Output("load-mass", "value"),
    Input("load-concentration", "value"),
    Input("load-volume", "value"),
)
def calculate_load_mass(load_concentration, load_volume):
    try:
        load_concentration = load_concentration or 0
        load_volume = load_volume or 0

        load_mass = load_concentration * load_volume
        load_mass = round(load_mass,2)
        return load_mass
    except Exception as e:
        print(f"Error calculating Load Mass: {e}")
        return ""


@app.callback(
    Output("uf1-mass", "value"),
    Input("load-mass", "value"),
    Input("uf1-target-concentration", "value"),
)
def calculate_target_reservoir_mass(load_mass, target_concentration):
    try:
        load_mass = load_mass or 0
        target_concentration = target_concentration or 1
        target_reservoir_mass = load_mass / target_concentration
        target_reservoir_mass = round(target_reservoir_mass,2)
        return target_reservoir_mass
    except Exception as e:
        print(f"Error calculating Target Reservoir Mass: {e}")
        return ""


@app.callback(
    Output("permeate-mass", "value"),
    Input("diavolumes", "value"),
    Input("uf1-mass", "value"),
    prevent_initial_call=True
)
def calculate_target_permeate_mass(diavolumes, target_reservoir_mass):
    try:
        diavolumes = diavolumes or 0
        target_reservoir_mass = target_reservoir_mass or 0
        target_permeate_mass = diavolumes * target_reservoir_mass
        return target_permeate_mass
    except Exception as e:
        print(f"Error calculating Target Permeate Mass: {e}")
        return ""


@app.callback(
    Output("target-flow-rate", "value"),
    Output("p2500-setpoint", "value"),
    Output("p3000-setpoint", "value"),
    Input("lmh-target", "value"),
    Input("cassette-select", "value"),
    prevent_initial_call=True
)
def calculate_flow_rate(lmh_target, cassette):
    try:
        filter_area = float(cassette) or 0
        print(filter_area)
        lmh_target = lmh_target or 0

        flow_rate = (lmh_target * filter_area) * 1000 / 60
        flow_rate = round(flow_rate, 2
                          )
        target_p2500_setpoint = (flow_rate / 1667) * 100
        target_p2500_setpoint = round(target_p2500_setpoint, 2
                                      )
        target_p3000_setpoint = (target_p2500_setpoint / 200) * 100
        target_p3000_setpoint = round(target_p3000_setpoint, 2)

        print(f'flowrate{flow_rate},target p 2500{target_p2500_setpoint},target p 3000{target_p3000_setpoint}')
        return flow_rate, target_p2500_setpoint, target_p3000_setpoint
    except Exception as e:
        print(f"Error calculating Target Permeate Mass: {e}")
        return ""


@app.callback(
    Output("product-mass", "value"),
    Output("yield", "value"),
    Input("final-volume", "value"),
    Input("final-concentration", "value"),
    Input("load-mass", "value"),

    prevent_initial_call=True
)
def calculate_flow_rate(final_volume, final_concentration, load_mass):
    try:
        final_volume = final_volume or 0
        final_concentration = final_concentration or 0
        load_mass = load_mass or 1

        product_mass = final_volume * final_concentration
        product_mass = round(product_mass, 2)

        recovery = product_mass / load_mass * 100
        recovery = round(recovery,2)

        return product_mass, recovery
    except Exception as e:
        print(f"Error calculating Target Permeate Mass: {e}")
        return ""


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
    State("load-mass", "value"),
    State("uf1-target-concentration", "value"),
    State("uf1-mass", "value"),
    State("diavolumes", "value"),
    State("permeate-mass", "value"),
    State("lmh-target", "value"),
    State("target-flow-rate", "value"),
    State("p2500-setpoint", "value"),
    State("p3000-setpoint", "value"),
    State("final-volume", "value"),
    State("final-concentration", "value"),
    State("product-mass", "value"),
    State("yield", "value"),

    prevent_initial_call=True
)
def handle_import(n_clicks, contents, molecule_name, experiment_name, experiment_notes,
                  cassette_type, load_concentration, load_volume, load_mass, uf1_target_concentration,
                  uf1_target_mass, diavolumes, target_permeate_mass, target_lmh, target_flowrate, p2500_setpoint,
                  p3000_setpoint, final_volume, final_concentration, product_mass, recovery):
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
        load_mass=load_mass ,
        target_diafiltration_concentration=uf1_target_concentration,
        uf1_target_reservoir_mass=uf1_target_mass,
        diavolumes=diavolumes,
        permeate_target_mass=target_permeate_mass,
        diafiltration_volume_required=target_permeate_mass * 1.25,
        lmh_target=target_lmh,
        target_flow_rate=target_flowrate,
        target_p2500_setpoint=p2500_setpoint,
        target_p3000_setpoint=p3000_setpoint,
        final_volume=final_volume,
        final_concentration=final_concentration,
        product_mass=product_mass,
        yield_percentage=recovery
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
