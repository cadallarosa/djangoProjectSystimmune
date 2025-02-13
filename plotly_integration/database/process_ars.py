import os
import sqlite3
import csv
import pandas as pd
import shutil
import config
from tqdm import tqdm


def convert_dict_to_df(metadata_dict):
    if metadata_dict is None:
        return None  # Return None if there's no metadata

    # Convert the dictionary into a DataFrame
    metadata_df = pd.DataFrame([metadata_dict])

    # Optionally, you can set column order or do further validation here
    return metadata_df


def insert_metadata_to_db(metadata_df, cursor):
    # Loop through the DataFrame and insert each row into the database
    for _, row in metadata_df.iterrows():
        # Check if the entry already exists (use result_id as the unique identifier)
        cursor.execute(
            """
            SELECT result_id 
            FROM sample_metadata 
            WHERE result_id = ? 
            """,
            (row["Result Id"],),
        )
        existing_entry = cursor.fetchone()

        if not existing_entry:
            # List of column names in the table
            column_names = [
                "Result Id", "System Name", "Project Name", "Sample Prefix", "Sample Number",
                "Sample Suffix", "Sample Type", "Sample Name", "Sample Set Id", "Sample Set Name",
                "Date Acquired", "Acquired By", "Run Time", "Processing Method",
                "Processed Channel Description", "Injection Volume", "Injection Id",
                "Column Name", "Column Serial Number", "Instrument Method Id", "Instrument Method Name"
            ]

            # Dynamically retrieve values from the DataFrame row
            values = [row.get(col) for col in column_names]

            # Insert a new record if it doesn't exist
            cursor.execute(
                f"""
                INSERT INTO sample_metadata ({', '.join([col.lower().replace(' ', '_') for col in column_names])})
                VALUES ({', '.join(['?' for _ in column_names])})
                """,
                values,
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
    # print(metadata_dict)
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
        elif check and any(keyword in row for keyword in ["ACQUITY TUV ChA","2998 Ch1 280nm@6.0nm"]):
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

            # print(df)
            return df

    return None


def insert_peak_results_to_db(peak_results_df, cursor):
    # Loop through each row of the peak_results DataFrame
    for index, row in peak_results_df.iterrows():
        # Check if the peak result already exists using the result_id and peak_name
        cursor.execute(
            """
            SELECT result_id
            FROM peak_results
            WHERE result_id = ? AND peak_retention_time = ?
            """,
            (row["result_id"], row["peak_retention_time"]),
        )
        existing_entry = cursor.fetchone()

        if not existing_entry:
            # Dynamically retrieve the values from the DataFrame row
            values = [
                row["result_id"], row["channel_name"], row["peak_name"],
                row["peak_retention_time"], row["peak_start_time"], row["peak_end_time"],
                row["area"], row["percent_area"], row["height"], row["asym_at_10"],
                row["plate_count"], row["res_hh"]
            ]

            # Insert the new peak result into the database
            cursor.execute(
                """
                INSERT INTO peak_results (result_id, channel_name, peak_name, peak_retention_time,
                                          peak_start_time, peak_end_time, area, percent_area, height,
                                          asym_at_10, plate_count, res_hh)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
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


def process_files(directory, db_name, reported_folder):
    # Ensure the Reported folder exists
    os.makedirs(reported_folder, exist_ok=True)

    # Get the list of .ars files
    files = [f for f in os.listdir(directory) if f.endswith(".ars")]

    # List to hold files that need to be moved
    files_to_move = []

    # Establish the database connection and cursor
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

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
            process_file(file_path, db_name, cursor)  # This will handle metadata extraction, conversion, and DB insertion

            # Extract peak results using the result_id (assuming result_id comes from process_file)
            metadata_dict, result_id = extract_metadata(file_path)
            if result_id != 0:
                peak_results_df = extract_peak_results(file_path, result_id)

                # Step 2: Insert peak results into the DB if the dataframe is not None
                if peak_results_df is not None:
                    insert_peak_results_to_db(peak_results_df, cursor)
                else:
                    print(f"No peak result data found for file: {filename}")

            # Add the file to the list of files to move
            files_to_move.append(file_path)

            files_processed = True

    # Commit all changes and close the connection
    conn.commit()

    # Step 3: Move all processed files to the Reported folder in bulk
    for file_path in files_to_move:
        shutil.move(file_path, os.path.join(reported_folder, os.path.basename(file_path)))

    # Close the connection
    conn.close()

