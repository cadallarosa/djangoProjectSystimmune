import base64
import io
import re
import numpy as np
import pandas as pd
from dash import dcc, html, Input, Output, State, dash_table
from django.db import IntegrityError
from django_plotly_dash import DjangoDash
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from plotly_integration.models import NovaFlex2

# Initialize the Dash app
app = DjangoDash('NovaFlex2DataUploadApp')

# Define Layout
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f4f7f6",
        "padding": "20px",
        "maxWidth": "1000px",
        "margin": "auto",
        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "borderRadius": "8px"
    },
    children=[
        html.H1(
            "NovaFlex2 Data Upload",
            style={
                "textAlign": "center",
                "color": "#0047b3",
                "marginBottom": "20px"
            }
        ),

        # File Upload Section
        html.Div(
            style={"textAlign": "center", "marginBottom": "20px"},
            children=[
                dcc.Upload(
                    id='upload-data',
                    children=html.Button(
                        '📂 Upload Excel File',
                        style={
                            "backgroundColor": "#0047b3",
                            "color": "white",
                            "padding": "10px 20px",
                            "border": "none",
                            "borderRadius": "5px",
                            "cursor": "pointer",
                            "fontSize": "16px"
                        }
                    ),
                    multiple=False
                ),
                html.Div(id='file-name', style={"marginTop": "10px", "fontWeight": "bold", "color": "green"})
            ]
        ),

        # Preview Data Table
        html.H3("Preview Data", style={"color": "#0047b3", "marginTop": "20px"}),
        dash_table.DataTable(
            id='data-preview',
            columns=[],  # Populated dynamically
            data=[],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#0047b3",
                "color": "white",
                "fontWeight": "bold"
            },
            style_cell={
                "padding": "10px",
                "textAlign": "center",
                "borderBottom": "1px solid #ccc"
            },
            style_data={"backgroundColor": "white", "color": "#333"}
        ),

        # Import Button (Initially Hidden)
        html.Div(
            style={"textAlign": "center", "marginTop": "20px"},
            children=[
                html.Button(
                    "⬇️ Import Data to Database",
                    id="save-button",
                    n_clicks=0,
                    style={
                        "display": "none",
                        "backgroundColor": "#28a745",
                        "color": "white",
                        "padding": "10px 20px",
                        "border": "none",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "16px"
                    }
                )
            ]
        ),

        # Import Status
        html.Div(
            id='save-status',
            style={
                "textAlign": "center",
                "marginTop": "20px",
                "fontSize": "18px",
                "fontWeight": "bold"
            }
        )
    ]
)


# Function to parse and clean uploaded Excel file
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    file_path = default_storage.save(f"uploads/{filename}", ContentFile(decoded))

    # Read the first sheet of Excel file
    xls = pd.ExcelFile(default_storage.path(file_path))
    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

    # Remove first row (which contains units)
    df_cleaned = df.iloc[1:].reset_index(drop=True)

    # Select relevant columns for database import
    relevant_columns = [
        "Date & Time", "Sample ID", "Sample Type", "Gln", "Glu", "Gluc", "Lac",
        "NH4+", "pH", "PO2", "PCO2", "Osm"
    ]
    df_cleaned = df_cleaned[relevant_columns]

    # Rename columns to match database model fields
    df_cleaned.rename(columns={
        "Date & Time": "date_time",
        "Sample ID": "sample_id",
        "Sample Type": "sample_type",
        "NH4+": "nh4",
        "PO2": "po2",
        "PCO2": "pco2",
        "Osm": "osm",
        "Gln": "gln",
        "Glu": "glu",
        "Gluc": "gluc",
        "Lac": "lac"
    }, inplace=True)

    # Convert date column to datetime
    df_cleaned["date_time"] = pd.to_datetime(df_cleaned["date_time"], errors="coerce")

    # Ensure numeric columns are properly converted
    numeric_columns = ["gln", "glu", "gluc", "lac", "nh4", "pH", "po2", "pco2", "osm"]
    df_cleaned[numeric_columns] = df_cleaned[numeric_columns].apply(pd.to_numeric, errors="coerce")

    # Auto-assign sample_type based on sample_id prefix
    def assign_sample_type(sample_id):
        if isinstance(sample_id, str):  # Ensure it's a string
            if sample_id.startswith("E"):
                return "1"
            elif sample_id.startswith("S"):
                return "2"
        return "3"  # Default if neither condition is met

    df_cleaned["sample_type"] = df_cleaned["sample_id"].apply(assign_sample_type)

    return df_cleaned


# Callback to read and preview the uploaded file
@app.callback(
    [Output('data-preview', 'columns'),
     Output('data-preview', 'data'),
     Output('file-name', 'children'),
     Output('save-button', 'style')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_output(contents, filename):
    if contents:
        try:
            df_cleaned = parse_contents(contents, filename)

            # Convert dataframe to DataTable format
            columns = [{"name": i, "id": i} for i in df_cleaned.columns]
            data = df_cleaned.to_dict('records')

            return columns, data, f"✅ File Uploaded: {filename}", {'display': 'block'}

        except Exception as e:
            return [], [], f"❌ Error reading file: {str(e)}", {'display': 'none'}

    return [], [], "No file uploaded.", {'display': 'none'}

def parse_sample_name(sample_name):
    """
    Parses the sample ID into structured components.

    Example mappings:
    - E47D00SF-1 -> {'experiment': 'E47', 'day': 0, 'reactor_type': 'SF', 'reactor_number': 1, 'special': ''}
    - E47D01BRX02 PREFEED -> {'experiment': 'E47', 'day': 1, 'reactor_type': 'BRX', 'reactor_number': 2, 'special': 'PRE'}
    """

    match = re.match(
        r"(?P<experiment>E\d{2})D(?P<day>\d{2})(?P<reactor_type>SF|BRX|BR)[-_]*(?P<reactor_number>\d+)\s*(?P<special>PREFEED|POSTFEED|PREINOC|POSTINOC)?",
        sample_name, re.IGNORECASE
    )

    # If first pattern fails, try alternate format
    if not match:
        match = re.match(
            r"(?P<experiment>E\d{2})D(?P<day>\d{2})(?P<reactor_type>SF|BRX|BR)\s*(?P<special>PREFEED|POSTFEED|PREINOC|POSTINOC)[-_]*(?P<reactor_number>\d+)",
            sample_name, re.IGNORECASE
        )

    # If still no match, return defaults
    if not match:
        print(f"⚠️ Could not parse sample: {sample_name}")
        return {
            "experiment": None,
            "day": None,
            "reactor_type": None,
            "reactor_number": None,
            "special": ""
        }


    parsed_data = match.groupdict()

    # Convert numeric fields
    parsed_data["day"] = int(parsed_data["day"]) if parsed_data["day"] else None
    parsed_data["reactor_number"] = int(parsed_data["reactor_number"]) if parsed_data["reactor_number"] else None

    # Normalize `special` field (PRE/POST labels)
    pre_post_map = {
        "PREFEED": "PRE",
        "PREINOC": "PRE",
        "POSTFEED": "POST",
        "POSTINOC": "POST"
    }
    parsed_data["special"] = pre_post_map.get(parsed_data["special"].upper(), "") if parsed_data["special"] else ""

    return parsed_data

@app.callback(
    Output('save-status', 'children'),
    Input('save-button', 'n_clicks'),
    State('data-preview', 'data'),
    prevent_initial_call=True
)
def save_to_db(n_clicks, data):
    if not data:
        return "No data to import."

    try:
        df = pd.DataFrame(data)

        # Convert date_time to proper format
        df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')

        # Replace NaN values with None (NULL) for MySQL compatibility
        df = df.replace({np.nan: None})

        for _, row in df.iterrows():
            parsed_sample = parse_sample_name(row["sample_id"])  # Parse sample ID
            # Use update_or_create to replace duplicates
            NovaFlex2.objects.update_or_create(
                date_time=row["date_time"],
                sample_id=row["sample_id"],
                defaults={
                    "sample_type": row["sample_type"],
                    "gln": row["gln"],
                    "glu": row["glu"],
                    "gluc": row["gluc"],
                    "lac": row["lac"],
                    "nh4": row["nh4"],
                    "pH": row["pH"],
                    "po2": row["po2"],
                    "pco2": row["pco2"],
                    "osm": row["osm"],

                    # Save parsed sample data
                    "experiment": parsed_sample["experiment"],
                    "day": parsed_sample["day"],
                    "reactor_type": parsed_sample["reactor_type"],
                    "reactor_number": parsed_sample["reactor_number"],
                    "special": parsed_sample["special"]
                }
            )

        return "✅ Data successfully imported, and duplicates were updated!"

    except Exception as e:
        return f"❌ Error saving to database: {str(e)}"