from datetime import datetime
import os
import re
import sqlite3
import csv
import pandas as pd
import shutil
import config
from tqdm import tqdm
from django.db import connection, transaction
from plotly_integration.models import SampleMetadata, PeakResults

# ✅ Database Settings
USE_ORM = True  # Change to False for raw SQL


def convert_runlog_timestamp(timestamp_str):
    """
    Converts 'M/D/YYYY h:mm:ss AM/PM PST' → 'YYYY-MM-DD HH:MM:SS' (MySQL-compatible).
    Strips timezone and assumes UTC.
    """

    if not timestamp_str or not isinstance(timestamp_str, str):
        print(f"⚠️ Invalid timestamp: {timestamp_str}. Using current time.")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # ✅ Default to current timestamp

    # ✅ Remove timezone part (last word)
    timestamp_parts = timestamp_str.strip().rsplit(" ", 1)

    if len(timestamp_parts) > 1:
        timestamp_str = timestamp_parts[0]  # ✅ Removes last part (timezone)

    try:
        # ✅ Parse the date assuming "M/D/YYYY h:mm:ss AM/PM" format
        dt = datetime.strptime(timestamp_str, "%m/%d/%Y %I:%M:%S %p")
        formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')  # ✅ Convert to MySQL format
        print(f"✅ Converted Timestamp: {timestamp_str} → {formatted_timestamp}")
        return formatted_timestamp
    except ValueError:
        print(f"⚠️ Invalid timestamp format: {timestamp_str}. Using current time.")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def clean_run_time(run_time):
    """
    Cleans '18.00 Minutes' → 18.00 (float).
    Assumes the format is always 'XX.XX Minutes'.
    """
    if not run_time or run_time == '':
        return None  # ✅ Handle empty values

    if isinstance(run_time, (int, float)):
        return float(run_time)  # ✅ Already a number

    if isinstance(run_time, str) and " Minutes" in run_time:
        try:
            return float(run_time.replace(" Minutes", "").strip())  # ✅ Remove ' Minutes' and convert to float
        except ValueError:
            print(f"⚠️ Error converting run_time: {run_time}")
            return None

    print(f"⚠️ Unexpected format for run_time: {run_time}. Returning None.")
    return None  # ✅ Fallback if format is unexpected


def clean_injection_volume(injection_volume):
    """
    Cleans '30.00 uL' → 30.00 (float).
    Assumes the format is always 'XX.XX uL'.
    """
    if not injection_volume or injection_volume == '':
        return None  # ✅ Handle empty values

    if isinstance(injection_volume, (int, float)):
        return float(injection_volume)  # ✅ Already a number

    if isinstance(injection_volume, str) and " uL" in injection_volume:
        try:
            return float(injection_volume.replace(" uL", "").strip())  # ✅ Remove ' uL' and convert to float
        except ValueError:
            print(f"⚠️ Error converting injection_volume: {injection_volume}")
            return None

    print(f"⚠️ Unexpected format for injection_volume: {injection_volume}. Returning None.")
    return None  # ✅ Fallback if format is unexpected


def convert_dict_to_df(metadata_dict):
    if metadata_dict is None:
        return None  # Return None if there's no metadata

    # Convert the dictionary into a DataFrame
    metadata_df = pd.DataFrame([metadata_dict])

    # Optionally, you can set column order or do further validation here
    return metadata_df


def extract_metadata(file_path):
    with open(file_path) as file_obj:
        reader = csv.reader(file_obj, delimiter='\t')
        data = [row for row in reader]

    # Extract metadata
    start_found = False
    metadata = []
    for row in data:
        if row == ['#', 'Inj Summary Report CAD Final  ']:
            start_found = True
            continue
        if start_found and ("Project Name:" in row and "Reported by User:" in row):
            break
        if start_found:
            metadata.append(row[0])

    # Process metadata into a dictionary
    metadata_dict = {
        key.strip(): value.strip()
        for row in metadata if ":" in row
        for key, value in [row.split(":", 1)]
    }

    # Extract `result_id` from "Injection Id" field in metadata
    result_id = int(metadata_dict.get("Injection Id", 0))

    # Check if the result_id is valid
    if result_id == 0:
        return None, None  # Return None to skip further processing
    # print(metadata_dict)
    metadata_dict['Result Id'] = result_id
    # print(metadata_dict)
    return metadata_dict, result_id


def insert_metadata(metadata_dict, use_orm=True):
    """
       Inserts metadata into the database using either Django ORM or raw SQL.
       Ensures all required fields are handled.
       """
    # ✅ Apply cleaning before inserting into the database
    metadata_dict["Run Time"] = clean_run_time(metadata_dict.get("Run Time"))
    metadata_dict["Injection Volume"] = clean_injection_volume(metadata_dict.get("Injection Volume"))
    metadata_dict["Date Acquired"] = convert_runlog_timestamp(metadata_dict.get("Date Acquired"))

    # ✅ Ensure numeric fields are converted properly
    metadata_dict["Sample Number"] = int(metadata_dict.get("Sample Number", 0) or 0)
    metadata_dict["Injection Id"] = int(metadata_dict.get("Injection Id", 0) or 0)
    metadata_dict["Instrument Method Id"] = int(metadata_dict.get("Instrument Method Id", 0) or 0)
    metadata_dict["Sample Set Id"] = int(metadata_dict.get("Sample Set Id", 0) or 0)
    # print(metadata_dict)
    if use_orm:
        # ✅ Insert using Django ORM
        SampleMetadata.objects.update_or_create(
            result_id=metadata_dict["Result Id"],
            defaults={
                "system_name": metadata_dict.get("System Name"),
                "project_name": metadata_dict.get("Project Name"),
                "sample_prefix": metadata_dict.get("Sample Prefix"),
                "sample_suffix": metadata_dict.get("Sample Suffix"),
                "sample_type": metadata_dict.get("Sample Type"),
                "sample_name": metadata_dict.get("Sample Name"),
                "sample_set_id": metadata_dict.get("Sample Set Id"),
                "sample_set_name": metadata_dict.get("Sample Set Name"),
                "date_acquired": metadata_dict["Date Acquired"],
                "acquired_by": metadata_dict.get("Acquired By"),
                "run_time": metadata_dict.get("Run Time"),
                "processing_method": metadata_dict.get("Processing Method"),
                "processed_channel_description": metadata_dict.get("Processed Channel Description"),
                "injection_volume": metadata_dict.get("Injection Volume"),
                "injection_id": metadata_dict.get("Injection Id"),
                "column_name": metadata_dict.get("Column Name"),
                "column_serial_number": metadata_dict.get("Column Serial Number"),
                "instrument_method_id": metadata_dict.get("Instrument Method Id"),
                "instrument_method_name": metadata_dict.get("Instrument Method Name"),
            }
        )
        print(f"✅ Metadata inserted via ORM for result_id {metadata_dict['Result Id']}")
    else:
        # ✅ Insert using Raw SQL
        sql = """
            REPLACE INTO sample_metadata (
                result_id, system_name, project_name, sample_prefix,
                sample_suffix, sample_type, sample_name, sample_set_id, sample_set_name,
                date_acquired, acquired_by, run_time, processing_method,
                processed_channel_description, injection_volume, injection_id,
                column_name, column_serial_number, instrument_method_id, instrument_method_name
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
            """

        values = (
            metadata_dict["Result Id"], metadata_dict.get("System Name"), metadata_dict.get("Project Name"),
            metadata_dict.get("Sample Prefix"),
            metadata_dict.get("Sample Suffix"), metadata_dict.get("Sample Type"),
            metadata_dict.get("Sample Name"), metadata_dict.get("Sample Set Id"),
            metadata_dict.get("Sample Set Name"), metadata_dict["date_acquired"], metadata_dict.get("Acquired By"),
            metadata_dict.get("Run Time"), metadata_dict.get("Processing Method"),
            metadata_dict.get("Processed Channel Description"), metadata_dict.get("Injection Volume"),
            metadata_dict.get("Injection Id"), metadata_dict.get("Column Name"),
            metadata_dict.get("Column Serial Number"), metadata_dict.get("Instrument Method Id"),
            metadata_dict.get("Instrument Method Name"),
        )

        with connection.cursor() as cursor:
            cursor.execute(sql, values)

    print(f"✅ Metadata inserted via Raw SQL for result_id {metadata_dict['Result Id']}")


def normalize_sample_names(metadata_dict):
    sample_name = metadata_dict.get("Sample Name", "").strip()
    sample_prefix = ""
    sample_suffix = ""

    # List of terms to check for in sample name (prefix or suffix)
    prefix_suffix_check = ["FB", "UP", "PD", "STD"]

    # Check for prefix dynamically (case insensitive)
    for term in prefix_suffix_check:
        if term in sample_name:  # Case-insensitive prefix check
            sample_prefix = term
            break  # Only one prefix is applied

    # Extract the sample number (digits in the middle of the name)
    sample_number = ''.join([c for c in sample_name if c.isdigit()])

    # Check if "n", "neut", or "neutralized" is present after the sample number
    for term in ["neutralized", "neut", "n"]:
        if term in sample_name.lower():
            sample_suffix = "N"
            break  # Once found, no need to check further for suffixes

    # Extract any remaining suffix (non-alphanumeric characters)
    remaining_suffix = ''.join([c for c in sample_name if not c.isalnum()]).strip()

    # Update the metadata dictionary with the extracted values
    metadata_dict["Sample Prefix"] = sample_prefix
    # metadata_dict["Sample Number"] = sample_number
    metadata_dict["Sample Suffix"] = sample_suffix or remaining_suffix

    return metadata_dict


def extract_peak_results(file_path, result_id):
    with open(file_path) as file_obj:
        reader = csv.reader(file_obj, delimiter='\t')
        data = [row for row in reader]

    # Define expected column headers
    expected_columns = [
        "Channel Name", "Name", "RT", "Area", "% Area", "Height",
        "Asym@10", "Plate Count", "Res (HH)", "Start Time", "End Time"
    ]

    report = []
    report.append(expected_columns)  # Force correct column order
    check = False  # Flag to start reading after the header
    for row in data:
        row = [col.strip() for col in row]  # Remove extra spaces

        # Detect the column header row (start of peak results)
        if "% Area" in row:
            check = True
            continue  # Skip the header row

        elif "(min)" in row:
            check = True
            continue  # Skip the header row

        # Start collecting peak data
        elif check and any(keyword in row for keyword in ["ACQUITY TUV ChA", "2998 Ch1 280nm@6.0nm"]):
            # print(row)
            # Ensure correct header row exists before adding data
            if not report:
                report.append(expected_columns)
                # print('not')

            # Align data properly
            while len(row) > len(expected_columns):
                row = row[1:]  # Shift left to match expected length
                # print(row)

            report.append(row)
    # print(report)
    # Convert collected peak data into a DataFrame
    if report:
        df = pd.DataFrame(data=report)
        # print(df)

        if not df.empty:
            # Assign the first row as column headers
            df.columns = df.iloc[0]
            df = df[1:].reset_index(drop=True)

            # Ensure valid column mappings
            column_mapping = {
                'Channel Name': 'channel_name',
                'Name': 'peak_name',
                'RT': 'peak_retention_time',
                'Area': 'area',
                '% Area': 'percent_area',
                'Height': 'height',
                'Asym@10': 'asym_at_10',
                'Plate Count': 'plate_count',
                'Res (HH)': 'res_hh',
                'Start Time': 'peak_start_time',
                'End Time': 'peak_end_time'
            }

            expected_columns = [
                'result_id', 'channel_name', 'peak_name', 'peak_retention_time', 'area',
                'percent_area', 'height', 'asym_at_10', 'plate_count',
                'res_hh', 'peak_start_time', 'peak_end_time'
            ]

            # Keep only necessary columns and rename them
            df = df.rename(columns=column_mapping)
            # print(df)
            # df = df[[col for col in df.columns if col in column_mapping]]

            # Add result_id column
            df["result_id"] = result_id
            # print(df)
            df = df[expected_columns]
            # Ensure all expected columns exist, filling missing ones with NaN
            for col in expected_columns:
                if col not in df:
                    df[col] = None
            df = df.drop_duplicates(subset=["peak_retention_time"], keep="first")
            # ✅ Remove rows where `peak_retention_time` is empty
            df = df[df["peak_retention_time"] != ""]
            print(df)
            print(df.head)
            return df

    return None


def string_to_float(value):
    """ Convert 'asym_at_10' field to float, allowing None values """
    try:
        return float(value) if value not in [None, ""] else None
    except ValueError:
        return None


def insert_peak_results(peak_results_df, use_orm=True):
    """
    Inserts peak results into MySQL using Django ORM or raw SQL.
    If (result_id, peak_retention_time) exists, REPLACE INTO ensures updates.
    """
    if peak_results_df is None or peak_results_df.empty:
        print("⚠️ No peak results to insert.")
        return

    if use_orm:
        # ✅ Insert using Django ORM with bulk_create (faster insertions)
        with transaction.atomic():
            peak_objects = [
                PeakResults(
                    result_id=row["result_id"],
                    channel_name=row["channel_name"],
                    peak_name=row["peak_name"],
                    peak_retention_time=row["peak_retention_time"],
                    peak_start_time=row["peak_start_time"],
                    peak_end_time=row["peak_end_time"],
                    area=row["area"],
                    percent_area=row["percent_area"],
                    height=row["height"],
                    asym_at_10=string_to_float(row["asym_at_10"]),
                    plate_count=string_to_float(row["plate_count"]),
                    res_hh=string_to_float(row["res_hh"])
                )
                for _, row in peak_results_df.iterrows()
            ]
            PeakResults.objects.bulk_create(peak_objects, ignore_conflicts=True)  # ✅ Faster insert
        print(f"✅ Inserted {len(peak_objects)} peak results via ORM.")

    else:
        # ✅ Insert using Raw SQL with REPLACE INTO (Best for MySQL)
        sql = """
        REPLACE INTO peak_results (
            result_id, channel_name, peak_name, peak_retention_time,
            peak_start_time, peak_end_time, area, percent_area, height,
            asym_at_10, plate_count, res_hh
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        values = [
            (
                row["result_id"], row["channel_name"], row["peak_name"],
                row["peak_retention_time"], row["peak_start_time"], row["peak_end_time"],
                row["area"], row["percent_area"], row["height"], row["asym_at_10"],
                row["plate_count"], row["res_hh"]
            )
            for _, row in peak_results_df.iterrows()
        ]

        with connection.cursor() as cursor:
            cursor.executemany(sql, values)  # ✅ Faster batch insert

        print(f"✅ Inserted {len(values)} peak results via Raw SQL.")


def process_file(file_path):
    # Step 1: Extract metadata into a dictionary
    metadata_dict, result_id = extract_metadata(file_path)

    if metadata_dict is None:
        print(f"Skipping file {file_path} due to invalid metadata.")
        return  # Skip this file if there's no valid metadata

    # Step 2: Normalize sample names (prefix, suffix, etc.)
    metadata_dict = normalize_sample_names(metadata_dict)

    # Step 3: Convert the dictionary to a DataFrame
    metadata_df = convert_dict_to_df(metadata_dict)

    if metadata_df is not None:
        # Step 4: Insert the metadata DataFrame into the DB
        insert_metadata(metadata_dict, use_orm=True)
    else:
        print(f"Skipping file {file_path} due to invalid DataFrame conversion.")


def process_files(directory, reported_folder):
    # Ensure the Reported folder exists
    os.makedirs(reported_folder, exist_ok=True)

    # Get the list of .ars files
    files = [f for f in os.listdir(directory) if f.endswith(".ars")]

    # List to hold files that need to be moved
    files_to_move = []

    files_processed = False
    if len(files) == 0:
        files_processed = True
    else:
        files_processed = False

    while not files_processed:
        # Wrap the files in a tqdm progress bar
        for filename in tqdm(files, desc="Processing Files", unit="file"):
            file_path = os.path.join(directory, filename)

            # Step 1: Process the file (extract metadata, convert to DataFrame, and insert)
            process_file(file_path)  # This will handle metadata extraction, conversion, and DB insertion

            # Extract peak results using the result_id (assuming result_id comes from process_file)
            metadata_dict, result_id = extract_metadata(file_path)
            if result_id != 0:
                peak_results_df = extract_peak_results(file_path, result_id)

                # Step 2: Insert peak results into the DB if the dataframe is not None
                if peak_results_df is not None:
                    insert_peak_results(peak_results_df, use_orm=True)
                else:
                    print(f"No peak result data found for file: {filename}")

            # Add the file to the list of files to move
            files_to_move.append(file_path)

            files_processed = True

    # Step 3: Move all processed files to the Reported folder in bulk
    for file_path in files_to_move:
        shutil.move(file_path, os.path.join(reported_folder, os.path.basename(file_path)))
