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
from plotly_integration.models import ViCellData

# Initialize the Dash app
app = DjangoDash('ViCellDataUploadApp')

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
            "Vi-Cell Data Upload",
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
    df_cleaned = df.iloc[0:].reset_index(drop=True)

    # Select relevant columns for database import
    relevant_columns = [
        "Analysis date/time", "Sample ID", "Cell count", "Viable cells", "Total (x10^6) cells/mL",
        "Viable (x10^6) cells/mL", "Viability (%)", "Average diameter (µm)", "Average viable diameter (µm)",
        "Average circularity", "Average viable circularity"
    ]
    df_cleaned = df_cleaned[relevant_columns]

    # Rename columns to match Django model fields
    df_cleaned.rename(columns={
        "Analysis date/time": "date_time",
        "Sample ID": "sample_id",
        "Cell count": "cell_count",
        "Viable cells": "viable_cells",
        "Total (x10^6) cells/mL": "total_cells_per_ml",
        "Viable (x10^6) cells/mL": "viable_cells_per_ml",
        "Viability (%)": "viability",
        "Average diameter (µm)": "average_diameter",
        "Average viable diameter (µm)": "average_viable_diameter",
        "Average circularity": "average_circularity",
        "Average viable circularity": "average_viable_circularity",

    }, inplace=True)

    # Convert date column to datetime
    df_cleaned["date_time"] = pd.to_datetime(df_cleaned["date_time"], errors="coerce")

    # Ensure numeric columns are properly converted
    numeric_columns = [
        "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml", "viability",
        "average_diameter", "average_viable_diameter", "average_circularity", "average_viable_circularity"
    ]
    df_cleaned[numeric_columns] = df_cleaned[numeric_columns].apply(pd.to_numeric, errors="coerce")

    # Assign sample_type based on predefined categories
    def assign_sample_type(sample_id):
        if isinstance(sample_id, str):  # Ensure it's a string
            if sample_id.startswith("E"):
                return 1  # UP
            elif sample_id.startswith("S"):
                return 2  # CLD
        return 3  # Uncategorized

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
    sample_name = str(sample_name)  # Convert to string if it's an integer

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

        new_records = []

        for _, row in df.iterrows():
            parsed_sample = parse_sample_name(row["sample_id"])  # Parse sample ID

            new_records.append(ViCellData(
                sample_id=row["sample_id"],
                date_time=row["date_time"],
                cell_count=row["cell_count"],
                viable_cells=row["viable_cells"],
                total_cells_per_ml=row["total_cells_per_ml"],
                viable_cells_per_ml=row["viable_cells_per_ml"],
                viability=row["viability"],
                average_diameter=row["average_diameter"],
                average_viable_diameter=row["average_viable_diameter"],
                average_circularity=row["average_circularity"],
                average_viable_circularity=row["average_viable_circularity"],


                # Parsed fields
                experiment=parsed_sample["experiment"],
                day=parsed_sample["day"],
                reactor_type=parsed_sample["reactor_type"],
                reactor_number=parsed_sample["reactor_number"],
                special=parsed_sample["special"],
                sample_type=row["sample_type"]
            ))

        # Perform bulk insert for new records
        if new_records:
            ViCellData.objects.bulk_create(new_records, ignore_conflicts=True)

        return f"Successfully inserted {len(new_records)} new records."

    except Exception as e:
        return f"Error importing data: {str(e)}"


