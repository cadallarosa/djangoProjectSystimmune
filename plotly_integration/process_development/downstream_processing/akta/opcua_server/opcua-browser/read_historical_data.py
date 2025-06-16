import os
import sys
import django
import numpy as np
import os
import sys

# Ensure this matches your project name and settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject.settings")

# Add the project path to sys.path
sys.path.append("C:\\Users\\cdallarosa\\DataAlchemy\\djangoProject")

import django
# django.setup()


import sys
import json
import os
import pandas as pd
from datetime import datetime
from opcua import Client, ua
import re
from plotly_integration.models import AktaChromatogram, AktaFraction, AktaRunLog, AktaNodeIds, AktaResult
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from dateutil import parser as date_parser

EXCLUDED_PATTERNS = [
    'UV 3_0', 'UV 2_0', '% Cond', 'System linear flow',
    'Cond temp', 'Sample linear flow', 'Conc Q1', 'Conc Q2',
    'Conc Q3', 'Conc Q4', 'Frac temp', 'UV cell path length',
    'Ratio UV2/UV1', 'Sample flow (CV/h)', 'System flow (CV/h)'
]
SPECIAL_TAGS = ['Run Log','Fraction', 'Injection']

# Security Configuration
PKI_DIR = r"C:\\Users\\cdallarosa\\DataAlchemy\\PythonProject1\\pki"
PKI_OWN_CERT = os.path.join(PKI_DIR, "own", "certs", "OWN.cer")
PKI_OWN_KEY = os.path.join(PKI_DIR, "own", "private", "uaexpert_privatekey.pem")
SERVER_CERT_PATH = os.path.join(PKI_DIR, "trusted", "certs", "HDAServer [84CD0A9C66CC7AA72575C3DBBDCFF83B0F84BCC1].der")
SERVER_URL = "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer"
USERNAME = "cdallarosa"
PASSWORD = "Default_710l"


def verify_security_files():
    return os.path.exists(PKI_OWN_CERT) and os.path.exists(PKI_OWN_KEY) and os.path.exists(SERVER_CERT_PATH)

def create_client():
    client = Client(SERVER_URL)
    client.application_uri = "urn:SI-CF8MJX3:UnifiedAutomation:UaExpert"
    security_string = f"Basic256Sha256,SignAndEncrypt,{PKI_OWN_CERT},{PKI_OWN_KEY},{SERVER_CERT_PATH}"
    client.set_security_string(security_string)
    client.set_user(USERNAME)
    client.set_password(PASSWORD)
    client.session_timeout = 30000
    client.uaclient.timeout = 30000
    client.watchdog_timeout = 60000
    return client

def clean_tag_name(node_id):
    base_name = node_id.split(":")[-1].replace("/", "_").replace(" ", "_")
    return f"{base_name}"

def should_include_tag(tag_name):
    return not any(pattern in tag_name for pattern in EXCLUDED_PATTERNS)


def extract_result_path(node_id):
    match = re.search(r"Folders/.*", node_id)
    return match.group(0) if match else "UnknownPath"


def save_dataframe(df, result_path, filename):
    folder_name = extract_result_path(result_path)
    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, filename)
    df.to_csv(file_path, index=False)


def fetch_historical_data(client, node_id, start_time, end_time):
    try:
        print(f"Reading historical data for node: {node_id}")
        node = client.get_node(node_id)
        hist_values = node.read_raw_history(start_time, end_time)
        print(f"Returned {len(hist_values)} values")
        data = []
        for value in hist_values:
            timestamp = value.SourceTimestamp.isoformat() if value.SourceTimestamp else ""
            val = value.Value.Value if value.Value.Value is not None else None
            status = value.StatusCode.name if value.StatusCode else ""
            data.append({"Timestamp": timestamp, "Value": val, "Status": status})
        return pd.DataFrame(data)
    except Exception as e:
        print("ERROR:", f"Error fetching historical data: {str(e)}")
        return None



def downsample_to_seconds(df, value_column="Value", interval="1s", method="mean"):
    """
    Downsamples a DataFrame to exact second intervals using a full second-based time grid.

    Parameters:
    - df: DataFrame with a 'Timestamp' column and a value column.
    - value_column: The column to downsample (e.g., 'Value').
    - interval: Resampling frequency (e.g., '1s').
    - method: Aggregation method: 'mean', 'sum', 'first'.

    Returns:
    - A DataFrame with a full second-aligned Timestamp column and the downsampled values.
    """
    if df.empty or "Timestamp" not in df.columns or value_column not in df.columns:
        return pd.DataFrame(columns=["Timestamp", value_column])

    df = df.copy()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp", value_column])
    df[value_column] = pd.to_numeric(df[value_column], errors="coerce")

    # Floor to exact seconds
    df["Timestamp"] = df["Timestamp"].dt.floor("1s")
    df.set_index("Timestamp", inplace=True)

    # Resample
    if method == "mean":
        df_resampled = df[[value_column]].resample(interval).mean()
    elif method == "sum":
        df_resampled = df[[value_column]].resample(interval).sum()
    elif method == "first":
        df_resampled = df[[value_column]].resample(interval).first()
    else:
        raise ValueError(f"Unsupported method: {method}")

    # Fill in missing seconds
    full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq=interval)
    df_resampled = df_resampled.reindex(full_index)

    # Return with reset index
    return df_resampled.reset_index().rename(columns={"index": "Timestamp"})



def parse_timestamp_with_microseconds(timestamp_str):
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f" if '.' in timestamp_str else "%Y-%m-%dT%H:%M:%S")
    except ValueError as e:
        print("ERROR:", f"Error parsing timestamp {timestamp_str}: {str(e)}")
        return None


def extract_full_result_metadata(df):
    if df is None or df.empty or "Value" not in df.columns:
        return None, None, None, None, None, None, None, None

    # Limit to first 15 rows
    values = df['Value'].dropna().astype(str).tolist()[:15]
    log_text = "\n".join(values)

    result_id = None
    result_path = None
    run_date = None
    user = None
    method = None
    column_volume_ml = None
    column_name = None

    for line in values:
        if "Batch ID:" in line:
            match = re.search(r"Batch ID:\s*([a-zA-Z0-9\-]+)", line)
            if match:
                result_id = match.group(1).strip()

        if "Result:" in line:
            # Step 1: Extract the full path
            match = re.search(r"Result:\s*(/.*?)(?:\s+User\b| at\b|$)", line)
            if match:
                full_path = match.group(1).strip()
                # Step 2: Trim back to the last `/`
                result_path = full_path.rsplit("/", 1)[0]

        if "Method:" in line:
            match = re.search(r"Method:\s*(.*?)\s*(Result:|$)", line)
            if match:
                method = match.group(1).strip()

        if "Method Run" in line:
            match = re.search(r"Method Run\s+([\d/]+\s+[\d:]+\s+[APMapm]+\s+[\-\+]\d{2}:?\d{2})", line)
            if match:
                run_date = match.group(1).strip()
                try:
                    run_date = date_parser.parse(run_date) if run_date else None
                except Exception as e:
                    print(f"❌ Failed to parse run_date: {run_date}, error: {e}")

        if "User" in line:
            match = re.search(r"User\s+(\w+)", line)
            if match:
                user = match.group(1).strip()

        if "Vc=" in line:
            match = re.search(r"Vc=([\d\.]+)\s*\{ml\}", line)
            if match:
                column_volume_ml = float(match.group(1))

        if re.search(r"[\d\.]+\s*cm\s*x\s*[\d\.]+\s*cm", line):
            match = re.search(r"([\d\.]+\s*cm\s*x\s*[\d\.]+\s*cm\s*[^\"\n]*)", line)
            if match:
                column_name = match.group(1).strip()

        print(result_id, result_path, run_date, user, method, column_volume_ml, column_name)

    return (
        result_id,
        result_path,
        run_date,
        user,
        method,
        column_volume_ml,
        column_name,
        log_text[:1024]
    )

def extract_result_path_from_nodeid(node_id: str) -> str:
    """
    Extracts the path from a nodeId, trimming off the tag and returning just the folder path.
    Example:
    'ns=2;s=13:Archive/OPCuser/.../DN 316 001:Chrom.1:Run Log' → 'Archive/OPCuser/.../DN 316 001/'
    """
    try:
        # Remove "ns=2;s=13:" prefix
        parts = node_id.split(":", 2)
        if len(parts) < 3:
            return "UnknownPath"
        path = parts[2]  # Get actual folder path
        if ":" in path:
            path = path.rsplit(":", 1)[0]  # Remove ":Chrom.1:Run Log"
        if "/" in path:
            path = path[:path.rfind("/") + 1]  # Keep up to last "/"
        return path
    except Exception as e:
        print(f"⚠️ Failed to extract path from nodeId '{node_id}': {e}")
        return "UnknownPath"


def clean_and_format_dataframe(df):
    if 'Status' in df.columns:
        df = df[df['Status'] == "Good"]
        df = df.drop(columns=['Status'])
    if 'Index' in df.columns:
        df = df.drop(columns=['Index'])
    return df

def insert_akta_chromatogram(df, result_id):
    df = df.replace({np.nan: None})
    AktaChromatogram.objects.filter(result_id=result_id).delete()
    records = []
    # Ensure timestamps are sorted
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors="coerce")
    # df = df.dropna(subset=['Timestamp'])
    df = df.sort_values('Timestamp').reset_index(drop=True)

    # Downsample to max 4000 points
    max_points = 4000

    if len(df) > max_points:
        indices = np.linspace(0, len(df) - 1, max_points, dtype=int)
        df_downsampled = df.iloc[indices].reset_index(drop=True)
        print(f"✅ Downsampled from {len(df)} to {len(df_downsampled)} rows")
        df = df_downsampled
        # df.to_csv("merged_downsampled_chromatogram.csv", index=False)
    else:
        print(f"ℹ️ No downsampling needed, only {len(df)} rows")

    # Calculate delta_t between rows (in seconds)
    df['delta_t'] = df['Timestamp'].diff().dt.total_seconds().fillna(0) / 60

    # Get flow columns as numeric
    df['sample_flow'] = pd.to_numeric(df.get('sample_flow'), errors='coerce').fillna(0.0)
    df['system_flow'] = pd.to_numeric(df.get('system_flow'), errors='coerce').fillna(0.0)


    # Initialize cumulative mL calculation
    ml = [0]
    for i in range(1, len(df)):
        delta = df.loc[i, 'delta_t']
        if df.loc[i, 'system_flow'] > 0:
            flow = df.loc[i, 'system_flow']
        elif df.loc[i, 'sample_flow'] > 0:
            flow = df.loc[i, 'sample_flow']
        else:
            flow = 0

        ml.append(ml[-1] + (delta * flow))

    df['ml'] = ml

    for _, row in df.iterrows():
        timestamp = parse_datetime(str(row["Timestamp"])) if pd.notna(row["Timestamp"]) else None
        if not timestamp:
            continue

        ml_value = row.get("ml")
        ml_value = None if pd.isna(ml_value) else float(ml_value)


        records.append(AktaChromatogram(
            date_time=timestamp,
            result_id=result_id,
            uv_1_280=row.get("uv_1") or row.get("UV_1_280"),
            uv_2_0=row.get("uv_2") or row.get("UV_2_280"),
            uv_3_0=row.get("uv_3") or row.get("UV_3_280"),
            cond=row.get("cond") or row.get("Cond"),
            conc_b=row.get("conc_b") or row.get("Conc_B"),
            pH=row.get("ph") or row.get("pH"),
            system_flow=row.get("system_flow") or row.get("System_flow"),
            system_pressure=row.get("system_pressure") or row.get("System_pressure"),
            sample_flow=row.get("sample_flow") or row.get("Sample_flow"),
            sample_pressure=row.get("sample_pressure") or row.get("Sample_pressure"),
            preC_pressure=row.get("prec_pressure") or row.get("PreC_pressure"),
            deltaC_pressure=row.get("deltac_pressure") or row.get("DeltaC_pressure"),
            postC_pressure=row.get("postc_pressure") or row.get("PostC_pressure"),
            frac_temp=None,
            ml=ml_value
        ))

    AktaChromatogram.objects.bulk_create(records)
    print(f"✅ AktaChromatogram: Replaced with {len(records)} rows for result_id {result_id}")

def insert_akta_fraction(df, result_id):
    print(df.columns)
    df = df.replace({np.nan: None})
    AktaFraction.objects.filter(result_id=result_id).delete()
    records = []
    for _, row in df.iterrows():
        timestamp = parse_datetime(str(row["Timestamp"])) if pd.notna(row["Timestamp"]) else None
        if not timestamp:
            continue
        records.append(AktaFraction(
            result_id=result_id,
            date_time=timestamp,
            fraction=row.get("Value"),
            ml=None
        ))

    AktaFraction.objects.bulk_create(records)
    print(f"✅ AktaFraction: Replaced with {len(records)} rows for result_id {result_id}")

def insert_akta_run_log(df, result_id):
    df = df.replace({np.nan: None})
    AktaRunLog.objects.filter(result_id=result_id).delete()
    records = []

    for _, row in df.iterrows():
        timestamp = parse_datetime(str(row["Timestamp"])) if pd.notna(row["Timestamp"]) else None
        if not timestamp:
            continue
        records.append(AktaRunLog(
            result_id=result_id,
            date_time=timestamp,
            log_text=row.get("Value"),
            ml=None
        ))

    AktaRunLog.objects.bulk_create(records)
    print(f"✅ AktaRunLog: Replaced with {len(records)} rows for result_id {result_id}")

def process_opcua_node_ids(start_time, end_time):
    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)

    if not verify_security_files():
        print("Security files missing")
        return

    client = create_client()
    client.connect()
    print("✅ Connected to OPC UA server")

    unimported = AktaNodeIds.objects.filter(imported=False)
    print(f"🔍 Found {unimported.count()} unimported results")

    for record in unimported:
        print(f"➡️ Processing record AktaNodeIds.result_id={record.result_id}")
        batch_id = None
        all_dataframes = []

        for field in ["run_log"] + ["fraction"]:
            node_id = getattr(record, field, None)
            if not node_id:
                continue

            df = fetch_historical_data(client, node_id, start_dt, end_dt)
            if df is None or df.empty:
                continue

            df = clean_and_format_dataframe(df)

            if field == "run_log":
                (
                    batch_id, result_path, run_date, user,
                    method, column_volume_ml, column_name, log_text
                ) = extract_full_result_metadata(df)

                # Extract result_path directly from run_log node ID
                result_path = node_id

                if not batch_id:
                    print(f"⚠️ No batch_id found in Run Log, skipping record {record.result_id}")
                    break

                insert_akta_run_log(df, batch_id)

            elif field == "fraction":
                if batch_id:
                    insert_akta_fraction(df, batch_id)


        if not batch_id:
            continue

        # Process chromatogram variables using working logic
        dfs = []
        for field in [
            "uv_1", "uv_2", "uv_3", "cond", "conc_b", "ph",
            "system_flow", "system_pressure", "sample_flow",
            "sample_pressure", "prec_pressure", "deltac_pressure", "postc_pressure"
        ]:
            node_id = getattr(record, field)
            if not node_id:
                continue

            df = fetch_historical_data(client, node_id, start_dt, end_dt)
            if df is not None and not df.empty:
                # df.to_csv(f"{field}.csv", index=False)
                df = clean_and_format_dataframe(df)

                # Ensure timestamps are sorted
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors="coerce")
                df = df.dropna(subset=['Timestamp'])
                df = df.sort_values('Timestamp').reset_index(drop=True)

                if "Value" in df.columns:
                    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
                    df = df.dropna(subset=["Value"])
                    df = downsample_to_seconds(df)

                df = df.rename(columns={"Value": clean_tag_name(field)})
                # df.to_csv(f"{field}_downsampled.csv", index=False)
                dfs.append(df)

        # Merge and save chromatogram data
        if dfs:
            merged = dfs[0]
            for next_df in dfs[1:]:
                merged = pd.merge(merged, next_df, on="Timestamp", how="outer")
            merged.to_csv("merged_chromatogram.csv", index=False)
            insert_akta_chromatogram(merged, batch_id)

        # Save AktaResult
        AktaResult.objects.update_or_create(
            result_id=batch_id,
            defaults={
                "result_path": result_path,
                "date": run_date,
                "user": user,
                "method": method,
                "column_volume": str(column_volume_ml) if column_volume_ml is not None else None,
                "column_name": column_name
            }
        )
        print(f"🧬 AktaResult saved: {batch_id}")

        record.imported = True
        record.save()
        print(f"✅ Finished processing AktaNodeIds.result_id={record.result_id}")

    client.disconnect()
    print("🔌 Disconnected from OPC UA server")
#
# # # Run in IDE
# #
# start_time = "2013-01-01T00:00:00"
# end_time = datetime.now().isoformat()
# # process_variables_file(variables_file, start_time, end_time)
# process_opcua_node_ids(start_time, end_time)


def main():
    start_time = "2013-01-01T00:00:00"
    end_time = datetime.now().isoformat()
    process_opcua_node_ids(start_time, end_time)

if __name__ == "__main__":
    main()