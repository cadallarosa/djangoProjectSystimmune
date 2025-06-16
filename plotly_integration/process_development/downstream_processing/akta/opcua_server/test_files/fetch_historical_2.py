import sys
import json
import os
import pandas as pd
from datetime import datetime
from opcua import Client
import re

# Configuration
JSON_FILE = "grouped_variables.json"
OUTPUT_DIR = "exported_data"
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
USERNAME = "OPCuser"
PASSWORD = "OPCuser_710l"

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

def extract_run_identifier(node_id):
    if ":Chrom.1:" in node_id:
        return node_id.split(":Chrom.1:")[0].split("/")[-1]
    parts = node_id.split('/')
    for part in reversed(parts):
        if part.strip() and not part.startswith("ns="):
            return part.split(":")[0] if ":" in part else part
    return "unknown_run"

def extract_result_path(node_id):
    match = re.search(r"Folders/.*", node_id)
    return match.group(0) if match else "UnknownPath"


def save_dataframe(df, result_path, filename):
    folder_name = extract_result_path(result_path)
    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, filename)
    df.to_csv(file_path, index=False)

def group_variables(variables):
    grouped = {'main_data': [], 'fraction': None, 'injection': None, 'run_log': None}
    for var in variables:
        tag_name = var['variableName']
        if not should_include_tag(tag_name):
            continue
        is_special = False
        for special in SPECIAL_TAGS:
            if tag_name.endswith(special):
                grouped[special.lower().replace(' ', '_')] = var
                is_special = True
                break
        if not is_special:
            grouped['main_data'].append(var)
    return grouped

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

def parse_timestamp_with_microseconds(timestamp_str):
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f" if '.' in timestamp_str else "%Y-%m-%dT%H:%M:%S")
    except ValueError as e:
        print("ERROR:", f"Error parsing timestamp {timestamp_str}: {str(e)}")
        return None

def downsample_to_second(df):
    if df.empty or 'Timestamp' not in df.columns:
        return df
    df['Timestamp'] = df['Timestamp'].apply(parse_timestamp_with_microseconds)
    df = df.dropna(subset=['Timestamp']).set_index('Timestamp')
    df = df.resample('1s').mean()
    return df.reset_index()

def extract_batch_id(df):
    if df is None:
        return None
    for val in df['Value']:
        if isinstance(val, str) and "Batch ID:" in val:
            match = re.search(r"Batch ID:\s*([a-zA-Z0-9\-]+)", val)
            if match:
                return match.group(1)
    return None

def clean_and_format_dataframe(df):
    if 'Status' in df.columns:
        df = df[df['Status'] == "Good"]
        df = df.drop(columns=['Status'])
    if 'Index' in df.columns:
        df = df.drop(columns=['Index'])
    return df

def process_variables_file(variables_file, start_time, end_time, output_dir="historical_data"):
    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)

    if not verify_security_files():
        print("ERROR: Security files verification failed")
        return

    client = create_client()
    client.connect()
    print("Successfully connected to server")

    with open(variables_file, 'r') as f:
        result_groups = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    for result_path, run_vars in result_groups.items():
        print(f"Processing result group: {result_path} with {len(run_vars)} variables")
        grouped = group_variables(run_vars)

        # 1. Fetch Run Log first to get batch_id
        batch_id = None
        run_log_var = grouped.get("run_log")
        if run_log_var:
            run_log_df = fetch_historical_data(client, run_log_var["nodeId"], start_dt, end_dt)
            run_log_df = clean_and_format_dataframe(run_log_df)
            batch_id = extract_batch_id(run_log_df)
            print(f'The Batch ID is {batch_id}')
            if batch_id:
                run_log_df["batch_id"] = batch_id
                save_dataframe(run_log_df, result_path, "Run_Log.csv")

        dfs = []
        for var in grouped["main_data"]:
            tag_name = var["variableName"]

            # Extra safety: skip if it's a special tag just in case it slipped through
            if any(tag in tag_name for tag in SPECIAL_TAGS):
                print(f"⚠️ Skipping special tag in main_data: {tag_name}")
                continue

            df = fetch_historical_data(client, var["nodeId"], start_dt, end_dt)
            if df is not None and not df.empty:
                df = clean_and_format_dataframe(df)

                # Ensure 'Value' is numeric before downsampling
                if 'Value' in df.columns:
                    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
                    df = df.dropna(subset=['Value'])

                df = downsample_to_second(df)
                df = df.rename(columns={'Value': clean_tag_name(tag_name)})

                # if batch_id:
                #     df["batch_id"] = batch_id

                dfs.append(df)

        # Merge and save main data
        if dfs:
            merged = dfs[0]
            for next_df in dfs[1:]:
                merged = pd.merge(merged, next_df, on="Timestamp", how="outer")
            # if batch_id:
            #     merged["batch_id"] = batch_id
            save_dataframe(merged, result_path, "merged.csv")
            print(f"Saved merged.csv for {result_path}")

        # Save fraction and injection tags separately
        for tag_key in ["fraction", "injection"]:
            var = grouped.get(tag_key)
            if var:
                df = fetch_historical_data(client, var["nodeId"], start_dt, end_dt)
                if df is not None and not df.empty:
                    df = clean_and_format_dataframe(df)
                    df = df.rename(columns={'Value': clean_tag_name(var['variableName'])})
                    # if batch_id:
                    #     df["batch_id"] = batch_id
                    save_dataframe(df, result_path, f"{tag_key}.csv")

    client.disconnect()
    print("Disconnected from server")


# Run in IDE
variables_file = JSON_FILE
start_time = "2013-01-01T00:00:00"
end_time = datetime.now().isoformat()
process_variables_file(variables_file, start_time, end_time)
