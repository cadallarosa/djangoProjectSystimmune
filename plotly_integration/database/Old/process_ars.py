import os
import sqlite3
import csv
import pandas as pd
import shutil
import config
from tqdm import tqdm
from plotly_integration.models import Report, SampleMetadata, PeakResults, TimeSeriesData
from datetime import datetime
import pytz  # For handling timezones

def validate_and_convert_float(value):
    """
    Validate and convert a value to a float, returning None for invalid values.
    """
    if value in [None, '', ' ']:  # Handle blank or None inputs
        return None
    try:
        return float(value)  # Attempt conversion
    except (ValueError, TypeError):
        return None

from dateutil import parser

def format_datetime(datetime_str):
    """
    Parse and format a date-time string into a Python datetime object.
    Handles timezone information like 'PST'.
    """
    try:
        # Use dateutil.parser for robust parsing of date-times with timezones
        date_obj = parser.parse(datetime_str)
        return date_obj
    except (ValueError, TypeError):
        raise ValueError(f"Invalid datetime format: {datetime_str}")

def extract_numeric(value):
    """
    Extract and return the numeric portion of a value as a float.
    If the value is invalid or does not contain a number, return None.
    """
    if value in [None, '', ' ']:
        return None
    try:
        # Extract numeric part from the string (e.g., '12.00 Minutes' -> 12.0)
        numeric_part = ''.join(c for c in value if c.isdigit() or c == '.')
        return float(numeric_part)
    except (ValueError, TypeError):
        return None

def convert_dict_to_df(metadata_dict):
    if metadata_dict is None:
        return None  # Return None if there's no metadata

    # Convert the dictionary into a DataFrame
    metadata_df = pd.DataFrame([metadata_dict])

    # Optionally, you can set column order or do further validation here
    return metadata_df


def insert_metadata_to_db(metadata_df):
    for _, row in metadata_df.iterrows():
        # Format the date_acquired field
        if row.get("Date Acquired"):
            try:
                row["Date Acquired"] = format_datetime(row["Date Acquired"])
            except ValueError as e:
                print(f"Skipping invalid date-time: {e}")
                continue  # Skip this record if the date-time is invalid

        # Process numeric fields like run_time
        row["Run Time"] = extract_numeric(row.get("Run Time"))
        row["Injection Volume"] = extract_numeric(row.get("Injection Volume"))

        SampleMetadata.objects.update_or_create(
            result_id=row["Result Id"],
            system_name=row["System Name"],
            defaults={
                "project_name": row.get("Project Name"),
                "sample_prefix": row.get("Sample Prefix"),
                "sample_number": row.get("Sample Number"),
                "sample_suffix": row.get("Sample Suffix"),
                "sample_type": row.get("Sample Type"),
                "sample_name": row.get("Sample Name"),
                "sample_set_id": row.get("Sample Set Id"),
                "sample_set_name": row.get("Sample Set Name"),
                "date_acquired": row.get("Date Acquired"),  # Now includes time
                "acquired_by": row.get("Acquired By"),
                "run_time": row.get("Run Time"),
                "processing_method": row.get("Processing Method"),
                "processed_channel_description": row.get("Processed Channel Description"),
                "injection_volume": row.get("Injection Volume"),
                "injection_id": row.get("Injection Id"),
                "column_name": row.get("Column Name"),
                "column_serial_number": row.get("Column Serial Number"),
                "instrument_method_id": row.get("Instrument Method Id"),
                "instrument_method_name": row.get("Instrument Method Name"),
            }
        )

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

    metadata_dict['Result Id'] = result_id
    return metadata_dict, result_id


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
    metadata_dict["Sample Number"] = sample_number
    metadata_dict["Sample Suffix"] = sample_suffix or remaining_suffix

    return metadata_dict


def extract_peak_results(file_path, result_id):
    with open(file_path) as file_obj:
        reader = csv.reader(file_obj, delimiter='\t')
        data = [row for row in reader]

    # Extract peak result data
    report = []
    check = False
    for row in data:
        if '% Area' in row:
            while row[1] != 'Channel Name':
                row = row[1:] + [row[0]]
            report.append(row)
            check = True
        elif 'ACQUITY TUV ChA' in row and check:
            if row[0] == '#':
                row = row[1:]
            report.append(row)

    if report:
        df = pd.DataFrame(data=report)

        if not df.empty:
            new_header = df.iloc[0]  # First row as header
            df = df[1:]  # Remove the header row from data
            df.columns = new_header  # Assign new header

            # Ensure valid column names by filtering out unexpected columns
            column_mapping = {
                'Result_Id': 'result_id',
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

            df = df[[col for col in df.columns if col in column_mapping]]
            df.drop(columns=[col for col in df.columns if '#' in str(col)], inplace=True)
            df.reset_index(drop=True, inplace=True)

            # Add result_id to the dataframe
            df['result_id'] = result_id

            # Rename columns to match the database schema
            df.rename(columns=column_mapping, inplace=True)

            # Ensure columns match the database schema
            df = df[expected_columns]
            return df
    return None


def insert_peak_results_to_db(peak_results_df):
    for _, row in peak_results_df.iterrows():
        PeakResults.objects.update_or_create(
            result_id=row["result_id"],
            peak_retention_time=validate_and_convert_float(row["peak_retention_time"]),
            defaults={
                "channel_name": row.get("channel_name", "").strip(),
                "peak_name": row.get("peak_name", "").strip(),
                "peak_start_time": validate_and_convert_float(row.get("peak_start_time")),
                "peak_end_time": validate_and_convert_float(row.get("peak_end_time")),
                "area": validate_and_convert_float(row.get("area")),
                "percent_area": validate_and_convert_float(row.get("percent_area")),
                "height": validate_and_convert_float(row.get("height")),
                "asym_at_10": validate_and_convert_float(row.get("asym_at_10")),
                "plate_count": validate_and_convert_float(row.get("plate_count")),
                "res_hh": validate_and_convert_float(row.get("res_hh")),
            }
        )

def process_file(file_path, db_name, cursor):
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
        insert_metadata_to_db(metadata_df, cursor)
    else:
        print(f"Skipping file {file_path} due to invalid DataFrame conversion.")


def process_ars_files(directory, reported_folder):
    """
    Process .ars files in the given directory.
    Moves processed files to the reported folder.
    """
    files = [f for f in os.listdir(directory) if f.endswith(".ars")]

    for filename in tqdm(files, desc="Processing .ars Files", unit="file"):
        file_path = os.path.join(directory, filename)

        # Extract metadata
        metadata_dict, result_id = extract_metadata(file_path)
        if metadata_dict:
            metadata_df = convert_dict_to_df(metadata_dict)
            insert_metadata_to_db(metadata_df)

        # Extract peak results
        if result_id:
            peak_results_df = extract_peak_results(file_path, result_id)
            if peak_results_df is not None:
                insert_peak_results_to_db(peak_results_df)

    # Move processed files
    for filename in files:
        shutil.move(os.path.join(directory, filename), os.path.join(reported_folder, filename))
