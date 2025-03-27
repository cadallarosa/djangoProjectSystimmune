import os
import re
import sqlite3
from django.db import transaction
import numpy as np
import pandas as pd
import shutil
import pytz
from tqdm import tqdm
from django.conf import settings
from dash import dcc, html, Input, Output
from django_plotly_dash import DjangoDash
from plotly_integration.models import (
    AktaChromatogram, AktaFraction, AktaRunLog, AktaResult
)
from datetime import datetime, timezone, timedelta
import re

# Get database path from Django settings
DB_PATH = settings.DATABASES['default']['NAME']

# Define file paths
BASE_DIR = os.path.join(settings.BASE_DIR, "plotly_integration", "data")
INPUT_DIR = r"S:\Shared\Chris Dallarosa\AKTA Database Imports\Chromatogram"  # Where .asc files are stored
PROCESSED_DIR = r"S:\Shared\Chris Dallarosa\AKTA Database Imported\Chromatogram"  # Where processed files go

# Ensure processed folder exists
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Create Django Dash app
app = DjangoDash("ImportAktaData")

# Layout of the web page
app.layout = html.Div(
    style={"textAlign": "center", "padding": "20px", "fontFamily": "Arial"},
    children=[
        html.H2("Akta Data Import"),
        html.Button("Start Import", id="start-import-btn", n_clicks=0, style={"padding": "10px", "fontSize": "16px"}),
        html.Div(id="import-status", style={"marginTop": "20px", "color": "blue"}),
    ]
)


def read_and_process_csv(file_path):
    """
    Reads and renames the chromatography CSV file for standardization.
    Ensures numeric columns are correctly converted.
    :param file_path: Path to the .asc file.
    :return: Processed DataFrame with renamed columns.
    """
    print(f"\n🔍 Reading file: {file_path}")

    # Read the .asc file (Auto-detect delimiter)
    df = pd.read_csv(file_path, sep=None, engine="python", skiprows=2, dtype=str, encoding="utf-8", on_bad_lines="skip")

    print("\n✅ Successfully loaded file!")

    # Define column renaming dictionary
    rename_dict = {
        "ml": "ml_1", "mAU": "UV 1_280", "ml.1": "ml_2", "mAU.1": "UV 2_0",
        "ml.2": "ml_3", "mAU.2": "UV 3_0", "ml.3": "ml_4", "mS/cm": "Cond",
        "ml.4": "ml_5", "%": "Conc B", "ml.5": "ml_6", "Unnamed: 11": "pH",
        "ml.6": "ml_7", "ml/min": "System flow", "ml.7": "ml_8", "cm/h": "System linear flow",
        "ml.8": "ml_9", "MPa": "System pressure", "ml.9": "ml_10", "Fraction": "Fraction",
        "ml.10": "ml_11", "Injection": "Injection", "ml.11": "ml_12", "°C": "Cond temp",
        "ml.12": "ml_13", "ml/min.1": "Sample flow", "ml.13": "ml_14", "cm/h.1": "Sample linear flow",
        "ml.14": "ml_15", "Logbook": "Run Log", "ml.15": "ml_16", "MPa.1": "Sample pressure",
        "ml.16": "ml_17", "MPa.2": "PreC pressure", "ml.17": "ml_18", "MPa.3": "DeltaC pressure",
        "ml.18": "ml_19", "MPa.4": "PostC pressure", "ml.19": "ml_20", "°C.1": "Frac temp",
        "Unnamed: 40": "Unused"
    }

    # Rename columns
    df.rename(columns=rename_dict, inplace=True)

    # Convert ml_* columns to numeric (floats)
    ml_cols = [col for col in df.columns if col.startswith("ml_")]
    for col in ml_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert to float, set errors to NaN

    print("\n✅ Converted ml columns to numeric.")

    print("\n✅ Renamed DataFrame Columns:\n", df.columns)
    return df


def downsample_data(df, interval=0.1):
    """
    Individually downsample each sensor column to a uniform ml interval.
    Keeps Fraction and Run Log separate.
    :param df: Input DataFrame containing ml and sensor columns.
    :param interval: Desired downsampling interval in mL.
    :return: Downsampled DataFrame, original Fraction & Run Log DataFrames.
    """
    # Identify ml & sensor columns
    ml_cols = [col for col in df.columns if col.startswith("ml_")]
    sensor_cols = [col for col in df.columns if col not in ml_cols]

    # Exclude `Fraction` (ml_10) and `Run Log` (ml_15) from interpolation
    interpolate_sensors = [col for col in sensor_cols if col not in ["Fraction", "Run Log"]]

    print("\n🔹 Interpolating Sensors:", interpolate_sensors)

    # -------------------------------
    # 1) Ensure all ml_* and sensor columns are numeric
    # -------------------------------
    for col in ml_cols + interpolate_sensors:
        df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert to float, set errors to NaN

    # Initialize downsampled DataFrame
    df_downsampled = pd.DataFrame({"ml": np.arange(df["ml_1"].min(), df["ml_1"].max(), interval)})

    # -------------------------------
    # 2) Downsample Each Sensor Individually
    # -------------------------------
    for i in range(1, 21):  # Loop over ml_1 to ml_20
        ml_col = f"ml_{i}"
        sensor_col = sensor_cols[i - 1] if i - 1 < len(sensor_cols) else None

        if sensor_col and sensor_col in interpolate_sensors:
            print(f"🔹 Downsampling: {sensor_col} using {ml_col}")

            # Drop NaNs and sort for interpolation
            sensor_data = df[[ml_col, sensor_col]].dropna().sort_values(by=ml_col)

            if sensor_data.empty:
                print(f"⚠️ Skipping {sensor_col}, no valid data for interpolation.")
                continue  # Skip if there is no data for interpolation

            # Ensure both columns are numeric again before interpolation
            sensor_data[ml_col] = pd.to_numeric(sensor_data[ml_col], errors="coerce")
            sensor_data[sensor_col] = pd.to_numeric(sensor_data[sensor_col], errors="coerce")

            # Interpolate sensor values to match downsampled ml axis
            df_downsampled[sensor_col] = np.interp(
                df_downsampled["ml"], sensor_data[ml_col], sensor_data[sensor_col]
            )

    # -------------------------------
    # 3) Store Fraction Data with Original X-Axis (ml_10)
    # -------------------------------
    if {"ml_10", "Fraction"}.issubset(df.columns):
        df_fraction = df[["ml_10", "Fraction"]].drop_duplicates().dropna().reset_index(drop=True)
        df_fraction.rename(columns={"ml_10": "ml"}, inplace=True)
    else:
        print(f"⚠️ Warning: 'Fraction' or 'ml_10' column is missing. Skipping fraction processing.")
        df_fraction = pd.DataFrame(columns=["ml", "Fraction"])  # ✅ Empty DataFrame with expected columns

    # -------------------------------
    # 4) Store Run Log Data with Original X-Axis (ml_15)
    # -------------------------------
    df_run_log = df[["ml_15", "Run Log"]].drop_duplicates().dropna().reset_index(drop=True)
    df_run_log.rename(columns={"ml_15": "ml"}, inplace=True)

    # -------------------------------
    # 5) Save Data
    # -------------------------------
    print("\n✅ Downsampled Sensor Data:\n", df_downsampled.head())
    print("\n✅ Fraction Data:\n", df_fraction.head())
    print("\n✅ Run Log Data:\n", df_run_log.head())

    # df_downsampled.to_csv("downsampled_chromatogram.csv", index=False)
    # df_fraction.to_csv("fraction_chromatogram.csv", index=False)
    # df_run_log.to_csv("run_log_chromatogram.csv", index=False)

    print("\n✅ Exported 'downsampled_chromatogram.csv', 'fraction_chromatogram.csv', and 'run_log_chromatogram.csv'")

    return df_downsampled, df_fraction, df_run_log

def convert_runlog_timestamp(timestamp_str):
    """
    Converts a timestamp from 'M/D/YYYY h:mm:ss AM/PM ±HH:MM' to MySQL-compatible format 'YYYY-MM-DD HH:MM:SS'
    """

    # Regex pattern to extract date, time, AM/PM, and timezone
    pattern = re.compile(r"(\d{1,2}/\d{1,2}/\d{4}) (\d{1,2}:\d{2}:\d{2} [APM]{2}) ([+-]\d{2}:\d{2})")
    match = pattern.match(timestamp_str)

    if not match:
        print(f"⚠️ Invalid timestamp format: {timestamp_str}")
        return None  # Return None if parsing fails

    date_part, time_part, tz_offset = match.groups()

    # Convert date + time to a datetime object
    dt = datetime.strptime(f"{date_part} {time_part}", "%m/%d/%Y %I:%M:%S %p")

    # Convert timezone offset to timedelta
    offset_hours, offset_minutes = map(int, tz_offset.split(":"))
    tz_delta = timedelta(hours=offset_hours, minutes=offset_minutes)

    # Apply timezone offset
    dt = dt.replace(tzinfo=timezone(tz_delta))

    # Convert to MySQL format (removes timezone)
    formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_timestamp

def extract_run_log_details(df_run_log):
    """
    Extracts Batch ID, Method Run timestamp, result path, user, and column ID from the Run Log column.
    :param df_run_log: DataFrame containing ml (X-axis) and Run Log data.
    :return: Extracted values as individual variables.
    """

    # Initialize variables
    timestamp, batch_id, method, result_path, user, column_id = None, None, None, None, None, None

    # Define regex patterns
    timestamp_pattern = re.compile(r"(\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [APM]{2} [-+\d:]+)")
    batch_id_pattern = re.compile(r"Batch ID:\s*([\w-]+)")
    method_pattern = re.compile(r"Method:\s*([\w\d_]+)")
    result_pattern = re.compile(r"Result:\s*(.*?)(?=\sUser|\Z)")
    user_pattern = re.compile(r"User\s([\w]+)")
    column_id_pattern = re.compile(r'Base CV, (.+)')

    for log in df_run_log["Run Log"].dropna():
        # Extract values
        if timestamp is None:
            timestamp_match = timestamp_pattern.search(log)
            timestamp = timestamp_match.group(1) if timestamp_match else None

        if batch_id is None:
            batch_id_match = batch_id_pattern.search(log)
            batch_id = batch_id_match.group(1) if batch_id_match else None

        if method is None:
            method_match = method_pattern.search(log)
            method = method_match.group(1) if method_match else None

        if result_path is None:
            result_match = result_pattern.search(log)
            result_path = result_match.group(1) if result_match else None

        if user is None:
            user_match = user_pattern.search(log)
            user = user_match.group(1) if user_match else None

        if column_id is None:
            column_id_match = column_id_pattern.search(log)
            column_id = column_id_match.group(1) if column_id_match else None

    converted_timestamp = convert_runlog_timestamp(timestamp)

    return converted_timestamp, batch_id, method, result_path, user, column_id


# Define function to insert Batch ID
def insert_batch_id(df_downsampled, df_fraction, df_run_log, batch_id):
    """
    Inserts the given Batch ID into the downsampled sensor data, fraction data, and run log DataFrames.

    :param df_downsampled: DataFrame containing downsampled sensor data.
    :param df_fraction: DataFrame containing fraction data.
    :param df_run_log: DataFrame containing run log data.
    :param batch_id: The Batch ID to be inserted.
    :return: Updated DataFrames with Batch ID.
    """
    # Add the Batch ID column to each DataFrame

    df_downsampled.insert(0, "result_id", batch_id)
    df_fraction.insert(0, "result_id", batch_id)
    df_run_log.insert(0, "result_id", batch_id)

    return df_downsampled, df_fraction, df_run_log


def process_akta_file_orm(file_path):
    """
    Loads Akta .asc file into DataFrames and inserts data into MySQL using Django ORM.
    """
    try:
        # Load and process file
        df = read_and_process_csv(file_path)
        df_downsampled, df_fraction, df_run_log = downsample_data(df, interval=0.1)
        timestamp, batch_id, method, result_path, user, column_id = extract_run_log_details(df_run_log)

        # Insert Batch ID into the DataFrames
        df_downsampled, df_fraction, df_run_log = insert_batch_id(df_downsampled, df_fraction, df_run_log, batch_id)

        # ✅ Use Django ORM to insert data in bulk
        with transaction.atomic():  # Ensures data integrity
            # 1️⃣ Insert into AktaChromatogram
            chromatogram_objects = [
                AktaChromatogram(
                    result_id=batch_id,
                    ml=row["ml"],
                    uv_1_280=row["UV 1_280"],
                    uv_2_0=row["UV 2_0"],
                    uv_3_0=row["UV 3_0"],
                    cond=row["Cond"],
                    conc_b=row["Conc B"],
                    pH=row["pH"],
                    system_flow=row["System flow"],
                    system_linear_flow=row["System linear flow"],
                    system_pressure=row["System pressure"],
                    cond_temp=row["Cond temp"],
                    sample_flow=row["Sample flow"],
                    sample_linear_flow=row["Sample linear flow"],
                    sample_pressure=row["Sample pressure"],
                    preC_pressure=row["PreC pressure"],
                    deltaC_pressure=row["DeltaC pressure"],
                    postC_pressure=row["PostC pressure"],
                    frac_temp=row["Frac temp"],
                )
                for _, row in df_downsampled.iterrows()
            ]
            AktaChromatogram.objects.bulk_create(chromatogram_objects)

            # 2️⃣ Insert into AktaFraction
            fraction_objects = [
                AktaFraction(
                    result_id=row["result_id"],
                    ml=row["ml"],
                    fraction=row["Fraction"]
                )
                for _, row in df_fraction.iterrows()
            ]
            AktaFraction.objects.bulk_create(fraction_objects)

            # 3️⃣ Insert into AktaRunLog
            run_log_objects = [
                AktaRunLog(
                    result_id=row["result_id"],
                    ml=row["ml"],
                    log_text=row["Run Log"]
                )
                for _, row in df_run_log.iterrows()
            ]
            AktaRunLog.objects.bulk_create(run_log_objects)

            # 4️⃣ Insert into AktaResult
            AktaResult.objects.create(
                result_id=batch_id,
                column_name=column_id.split(", ")[1] if column_id else None,
                column_volume=column_id.split(", ")[0].split("=")[1].split(" ")[0] if column_id else None,
                method=method,
                result_path=result_path,
                date=timestamp,
                user=user,
                system="system_name_here",  # Adjust based on your logic
            )

        return f"✅ Inserted {len(chromatogram_objects)} chromatogram rows, {len(fraction_objects)} fraction rows, and {len(run_log_objects)} run log rows from {file_path}"

    except Exception as e:
        return f"❌ Error processing {file_path}: {str(e)}"


def process_akta_file_raw_sql(file_path):
    """
    Loads Akta .asc file into DataFrames and inserts data into MySQL using raw SQL.
    """
    try:
        # Load and process file
        df = read_and_process_csv(file_path)
        df_downsampled, df_fraction, df_run_log = downsample_data(df, interval=0.1)
        timestamp, batch_id, method, result_path, user, column_id = extract_run_log_details(df_run_log)
        df_downsampled, df_fraction, df_run_log = insert_batch_id(df_downsampled, df_fraction, df_run_log, batch_id)

        # ✅ Connect to MySQL database
        from django.db import connection
        with connection.cursor() as cursor:
            # 1️⃣ Insert into akta_chromatogram
            chromatogram_sql = """
            INSERT INTO akta_chromatogram (
                result_id, ml, uv_1_280, uv_2_0, uv_3_0, cond, conc_b, pH, system_flow,
                system_linear_flow, system_pressure, cond_temp, sample_flow, sample_linear_flow,
                sample_pressure, preC_pressure, deltaC_pressure, postC_pressure, frac_temp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(chromatogram_sql, df_downsampled.values.tolist())

            # 2️⃣ Insert into akta_fraction
            fraction_sql = "INSERT INTO akta_fraction (result_id, ml, fraction) VALUES (%s, %s, %s)"
            cursor.executemany(fraction_sql, df_fraction.values.tolist())

            # 3️⃣ Insert into akta_run_log
            run_log_sql = "INSERT INTO akta_run_log (result_id, ml, log_text) VALUES (%s, %s, %s)"
            cursor.executemany(run_log_sql, df_run_log.values.tolist())

            # 4️⃣ Insert into akta_result
            result_sql = """
            INSERT INTO akta_result (result_id, column_name, column_volume, method, result_path, date, user, system)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(result_sql,
                           (batch_id, column_id, None, method, result_path, timestamp, user, "system_name_here"))

        return f"✅ Inserted data using raw SQL from {file_path}"

    except Exception as e:
        return f"❌ Error processing {file_path}: {str(e)}"


def process_all_files(use_orm=False):
    """
    Processes all Akta .asc files and moves them to the processed folder.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".asc")]
    if not files:
        return "No Akta files found."

    results = []
    for file_name in tqdm(files, desc="Processing Files", unit="file"):
        file_path = os.path.join(INPUT_DIR, file_name)
        if not os.path.exists(file_path):
            results.append(f"Skipping {file_name}: File not found.")
            continue

        if use_orm:
            result = process_akta_file_orm(file_path)
        else:
            result = process_akta_file_raw_sql(file_path)

        results.append(result)

        processed_path = os.path.join(PROCESSED_DIR, file_name)
        if os.path.exists(file_path):
            shutil.move(file_path, processed_path)

    return "\n".join(results)



@app.callback(
    Output("import-status", "children"),
    Input("start-import-btn", "n_clicks"),
    prevent_initial_call=True
)
def trigger_import(n_clicks):
    """ Callback to trigger import when button is pressed """
    return process_all_files(use_orm=True)  # ✅ Change to False for raw SQL
