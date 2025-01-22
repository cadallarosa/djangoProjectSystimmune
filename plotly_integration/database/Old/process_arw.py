import os
import sqlite3
import shutil
from tqdm import tqdm
import pandas as pd
from plotly_integration.models import Report, SampleMetadata, PeakResults, TimeSeriesData, ChromMetadata, SystemInformation


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
    """
    Parse .arw file to extract metadata and time-series data.
    Normalize keys to ensure consistent field naming.
    """
    chrom_metadata = {}
    data_points = []

    with open(file_path, "r") as file:
        lines = file.readlines()

        # Normalize headers
        header = [col.strip('"').strip().lower().replace(" ", "_") for col in lines[0].strip().split("\t")]
        data_row = [value.strip('"').strip() for value in lines[1].strip().split("\t")]

        # Populate chrom_metadata dictionary
        chrom_metadata = dict(zip(header, data_row))

        # Normalize specific keys for consistency
        if "samplename" in chrom_metadata:
            chrom_metadata["sample_name"] = chrom_metadata.pop("samplename")

        # Map Injection ID to Result ID if not already set
        if "injection_id" in chrom_metadata and "result_id" not in chrom_metadata:
            chrom_metadata["result_id"] = chrom_metadata["injection_id"]

        # Parse data points (remaining lines)
        for line in lines[2:]:
            if line.strip():
                time, measurement = map(float, line.strip().split("\t"))
                data_points.append((time, measurement))

    # Downsample the data points
    data_points = downsample_data(data_points, interval=0.0166667)  # Adjust interval as needed
    return chrom_metadata, data_points



def insert_into_database(chrom_metadata, data_points):
    """
    Insert chromatographic metadata and time-series data into the database using Django ORM.
    Ensures that sample_name is included in the ChromMetadata table.
    """
    # Query the SystemInformation table for channel mappings based on the system_name
    try:
        system_info = SystemInformation.objects.get(system_name=chrom_metadata["system_name"])
    except SystemInformation.DoesNotExist:
        print(f"System '{chrom_metadata['system_name']}' not found in SystemInformation table.")
        return

    # Map channels dynamically
    channel_to_column = {
        system_info.channel_1.lower(): "channel_1",
        system_info.channel_2.lower(): "channel_2",
        system_info.channel_3.lower(): "channel_3",
    }

    # Normalize file_channel_name for matching
    file_channel_name = chrom_metadata.get("channel", "").strip().lower()
    if file_channel_name not in channel_to_column:
        print(f"Skipping: Channel '{file_channel_name}' not recognized for system '{chrom_metadata['system_name']}'.")
        return

    target_column = channel_to_column[file_channel_name]

    # Validate result_id
    result_id = chrom_metadata.get("result_id")
    if not result_id:
        raise KeyError("Missing 'result_id' in chrom_metadata.")

    # Extract sample_name
    sample_name = chrom_metadata.get("sample_name", "").strip()
    if not sample_name:
        print(f"Warning: Missing 'sample_name' for result_id {result_id}. Defaulting to 'Unknown Sample'.")
        sample_name = "Unknown Sample"

    # Update or create ChromMetadata
    ChromMetadata.objects.update_or_create(
        result_id=result_id,
        system_name=chrom_metadata["system_name"],
        defaults={
            "sample_name": sample_name,  # Ensure sample_name is passed here
            "sample_set_name": chrom_metadata.get("sample_set_name"),
            "sample_set_id": chrom_metadata.get("sample_set_id"),
            target_column: file_channel_name,
        }
    )

    # Insert time-series data
    for _, row in data_points.iterrows():
        TimeSeriesData.objects.update_or_create(
            result_id=result_id,
            time=row["time_rounded"],
            defaults={
                "system_name": chrom_metadata["system_name"],
                target_column: row["measurement"],  # Update only the target channel
            }
        )

def process_arw_files(directory, reported_folder):
    """
    Process .arw files in the given directory.
    Moves processed files to the reported folder.
    """
    files = [f for f in os.listdir(directory) if f.endswith(".arw")]

    for filename in tqdm(files, desc="Processing .arw Files", unit="file"):
        file_path = os.path.join(directory, filename)
        try:
            # Parse file
            chrom_metadata, data_points = parse_arw_file(file_path)

            # Insert chromatographic metadata and time-series data
            if chrom_metadata and data_points is not None:
                insert_into_database(chrom_metadata, data_points)
        except KeyError as e:
            print(f"Skipping file {filename}: {e}")
            continue

    # Move processed files
    for filename in files:
        shutil.move(os.path.join(directory, filename), os.path.join(reported_folder, filename))
