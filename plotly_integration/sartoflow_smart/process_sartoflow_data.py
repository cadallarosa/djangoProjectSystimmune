import os
import sqlite3
import pandas as pd
import shutil

import pytz
from tqdm import tqdm
from django.conf import settings
from dash import dcc, html, Input, Output, State
from django_plotly_dash import DjangoDash

# Get database path from Django settings
DB_PATH = settings.DATABASES['default']['NAME']

# Define file paths
BASE_DIR = os.path.join(settings.BASE_DIR, "plotly_integration", "data")
INPUT_DIR = os.path.join(BASE_DIR, "Imports")  # Where CSV files are stored
PROCESSED_DIR = os.path.join(BASE_DIR, "Processed")  # Where processed files go

# Ensure processed folder exists
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Create Django Dash app
app = DjangoDash("ImportSartoflow")

# Layout of the web page
app.layout = html.Div(
    style={"textAlign": "center", "padding": "20px", "fontFamily": "Arial"},
    children=[
        html.H2("Sartoflow Data Import"),
        html.Button("Start Import", id="start-import-btn", n_clicks=0, style={"padding": "10px", "fontSize": "16px"}),
        html.Div(id="import-status", style={"marginTop": "20px", "color": "blue"}),
        dcc.Interval(id="progress-update", interval=1000, n_intervals=0, disabled=True),  # Progress refresh
    ]
)


def load_clean_csv(file_path):
    """ Reads and cleans Sartoflow CSV data """

    # Read CSV file without assuming headers
    df = pd.read_csv(file_path, delimiter=";", skiprows=2, header=None)

    # Print original detected columns for debugging
    print(f"Detected {len(df.columns)} columns in {file_path}")
    print("Original Data (first 5 rows):")
    print(df.head())  # Debugging: Check first few rows

    # Manually assign headers to ensure proper alignment
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
        "WIRC2100_Output", "WIRC2100_Setpoint", "WIRC2100_Mode"
    ]

    # Ensure we have the right number of columns
    df = df.iloc[:, :len(correct_headers)]

    # Assign headers
    df.columns = correct_headers

    # Drop rows where `BatchId` is NaN (i.e., any unwanted header rows)
    df = df.dropna(subset=["BatchId"])

    # # Convert datetime column & replace NaT with None
    # df["PDatTime"] = pd.to_datetime(df["PDatTime"], errors="coerce")
    #
    # # Define the target timezone
    # target_timezone = pytz.timezone("America/Los_Angeles")  # Change as needed
    #
    # # Convert to formatted datetime with timezone offset
    # df["PDatTime"] = df["PDatTime"].apply(lambda x: x.astimezone(target_timezone).strftime("%Y-%m-%d %H:%M:%S%z") if pd.notna(x) else None)

    # Replace NaN values with None for database insertion
    df = df.where(pd.notnull(df), None)

    # Ensure all columns are displayed
    pd.set_option("display.max_columns", None)  # Show all columns
    pd.set_option("display.width", 200)  # Prevent line breaks

    # Print first 30 rows
    print(df.head(30))
    return df


def process_sartoflow_file(file_path, conn):
    """ Processes a single Sartoflow CSV file and inserts data into the database """
    try:
        df = load_clean_csv(file_path)  # Load and clean the CSV file

        cursor = conn.cursor()
        insert_query = """
            INSERT INTO sartoflow_time_series_data (
                batch_id, pdat_time, process_time, ag2100_value, ag2100_setpoint,
                ag2100_mode, ag2100_output, dpress_value, dpress_output, dpress_mode,
                dpress_setpoint, f_perm_value, p2500_setpoint, p2500_value,
                p2500_output, p2500_mode, p3000_setpoint, p3000_mode, p3000_output,
                p3000_value, p3000_t, pir2600, pir2700, pirc2500_value,
                pirc2500_output, pirc2500_setpoint, pirc2500_mode, qir2000,
                qir2100, tir2100, tmp, wir2700, wirc2100_output, wirc2100_setpoint, wirc2100_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        batch_size = 1000
        records = [tuple(row) for row in df.itertuples(index=False, name=None)]

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()

        return f"Inserted {len(records)} records from {file_path}"
    except Exception as e:
        return f"Error processing {file_path}: {str(e)}"


def process_all_files():
    """ Processes all Sartoflow CSV files and moves them to the processed folder """
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]

    if not files:
        return "No Sartoflow files found."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=OFF;")

    results = []
    for file_name in tqdm(files, desc="Processing Files", unit="file"):
        file_path = os.path.join(INPUT_DIR, file_name)

        # Check if file still exists before processing
        if not os.path.exists(file_path):
            results.append(f"Skipping {file_name}: File not found.")
            continue

        result = process_sartoflow_file(file_path, conn)
        results.append(result)

        processed_path = os.path.join(PROCESSED_DIR, file_name)

        # Ensure file exists before moving
        if os.path.exists(file_path):
            shutil.move(file_path, processed_path)
        else:
            results.append(f"Warning: {file_name} was deleted before move.")

    conn.close()
    return "\n".join(results)

@app.callback(
    Output("import-status", "children"),
    Output("progress-update", "disabled"),
    Input("start-import-btn", "n_clicks"),
    prevent_initial_call=True
)
def trigger_import(n_clicks):
    """ Callback to trigger import when button is pressed """
    return process_all_files(), False
