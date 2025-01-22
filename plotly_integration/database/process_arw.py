import os
import sqlite3
import shutil
from tqdm import tqdm
import pandas as pd
# from database_table_creation_functions import query_channels_by_system

def query_channels_by_system(conn, system_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT channel_1, channel_2, channel_3
        FROM system_information
        WHERE system_name = ?;
    """, (system_name,))
    return cursor.fetchone()  # Returns a single matching row

def downsample_data(data_points, interval=0.0166667):
    """
    Downsample the time-series data to the specified interval using pandas.
    :param data_points: List of (time, measurement) tuples.
    :param interval: Desired sampling interval in minutes.
    :return: Downsampled pandas DataFrame.
    """
    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data_points, columns=["time", "measurement"])

    # Round the time to the nearest interval
    df['time_rounded'] = (df['time'] // interval) * interval

    # Group by the rounded time and compute the mean for each group
    downsampled = df.groupby('time_rounded')['measurement'].mean().reset_index()

    return downsampled  # Return the DataFrame without converting to a list


def parse_arw_file(file_path):
    
    chrom_metadata = {}
    data_points = []

    with open(file_path, "r") as file:
        lines = file.readlines()

        # Normalize headers
        header = [col.strip('"').strip().lower().replace(" ", "_") for col in lines[0].strip().split("\t")]
        data_row = [value.strip('"').strip() for value in lines[1].strip().split("\t")]

        # Populate chrom_metadata dictionary
        chrom_metadata = dict(zip(header, data_row))

        # Extract additional metadata
        chrom_metadata["system_name"] = chrom_metadata.get("system_name", "")
        chrom_metadata["sample_set_id"] = int(chrom_metadata.get("sample_set_id", 0))

        # Parse data points (remaining lines)
        for line in lines[2:]:
            if line.strip():
                time, measurement = map(float, line.strip().split("\t"))
                data_points.append((time, measurement))

    # Downsample the data points
    data_points = downsample_data(data_points, interval=0.0166667)  # Adjust interval as needed
    return chrom_metadata, data_points


def insert_into_database(conn, chrom_metadata, data_points):

    cursor = conn.cursor()
    channel_names = query_channels_by_system(conn, 'BENDER TUV')
    
    # Map Channel Name to Columns (case insensitive)
    channel_to_column = {
        f"{channel_names[0]}": "channel_1",
        f"{channel_names[1]}": "channel_2",
        f"{channel_names[2]}": "channel_3"
    }

    # Normalize file_channel_name for matching
    file_channel_name = chrom_metadata.get('channel', '').strip().lower()
    # print(f"Processing channel: '{file_channel_name}'")  # Debug print
    if file_channel_name not in channel_to_column:
        # print(f"Channel '{file_channel_name}' not recognized. Skipping insert.")
        return

    target_column = channel_to_column[file_channel_name]
    # print(f"Target column identified: {target_column}")  # Debug print

    # Check if row exists for the result_id
    check_query = """
        SELECT channel_1,channel_2,channel_3
        FROM chrom_metadata
        WHERE result_id = ?
    """
    cursor.execute(check_query, (chrom_metadata["injection_id"],))
    existing_row = cursor.fetchone()

    if existing_row:
        # Row exists; dynamically update only the target column
        update_query = f"""
                UPDATE chrom_metadata
                SET {target_column} = ?
                WHERE result_id = ?
            """
        # Ensure target_column is validated and safe
        if not target_column.isidentifier():
            raise ValueError("Invalid column name")

        cursor.execute(update_query, (file_channel_name, chrom_metadata["injection_id"]))

    else:
        # Row does not exist; insert new row with only the target column
        insert_query = f"""
            INSERT INTO chrom_metadata 
            (result_id, system_name, sample_name, sample_set_name, sample_set_id, {target_column})
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, (
            chrom_metadata["injection_id"],
            chrom_metadata["system_name"],
            chrom_metadata["samplename"],
            chrom_metadata["sample_set_name"],
            chrom_metadata["sample_set_id"],
            chrom_metadata.get('channel', '').strip().lower()
        ))
        # print(f"Inserted new row with column '{target_column}' set to 1")


    #Prepare Time-Series Data for Insert
    #Convert DataFrame to list of tuples (result_id, system_name, time, sensor_value)
    time_series_data = [
        (chrom_metadata["injection_id"], 
         chrom_metadata["system_name"], 
         row['time_rounded'], 
         row['measurement'])  # 'sensor_value' is assumed to exist in data_points
        for index, row in data_points.iterrows()
    ]
    
    # 4. Upsert Logic: Only Update the Target Column
    query = f"""
        INSERT INTO time_series_data (result_id, system_name, time, {target_column})
        VALUES (?, ?, ?, ?)
        ON CONFLICT(result_id, time) 
        DO UPDATE SET {target_column} = excluded.{target_column};
    """
    cursor.executemany(query, time_series_data)
    
    conn.commit()


def process_files(directory, db_name, reported_folder):
    # Open the database connection once
    conn = sqlite3.connect(db_name)

    # Ensure the Reported folder exists
    os.makedirs(reported_folder, exist_ok=True)

    # Get the list of .arw files
    files = [f for f in os.listdir(directory) if f.endswith(".arw")]

    # Process each file and insert data into the database
    for filename in tqdm(files, desc="Processing Files", unit="file"):
        file_path = os.path.join(directory, filename)

        # Parse the file
        chrom_metadata, data_points = parse_arw_file(file_path)

        # Insert data into the database
        insert_into_database(conn, chrom_metadata, data_points)

    # After all files are processed, perform the bulk file transfer
    for filename in files:
        shutil.move(os.path.join(directory, filename), os.path.join(reported_folder, filename))

    # Close the database connection after all files are processed
    conn.close()



