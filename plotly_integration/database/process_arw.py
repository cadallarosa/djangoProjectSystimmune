import os
import sqlite3
import shutil
from tqdm import tqdm
import pandas as pd
from django.db import connection, transaction
# from database_table_creation_functions import query_channels_by_system
from plotly_integration.models import ChromMetadata, TimeSeriesData, SystemInformation

# ✅ Choose Database Mode
USE_ORM = True  # Set to False for raw SQL

def query_channels_by_system(system_name, use_orm=True):
    """ Retrieves channel mapping for a given system name. """
    if use_orm:
        try:
            system_info = SystemInformation.objects.get(system_name=system_name)
            return [system_info.channel_1, system_info.channel_2, system_info.channel_3]
        except SystemInformation.DoesNotExist:
            return None
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT channel_1, channel_2, channel_3 
                FROM system_information 
                WHERE system_name = %s;
            """, [system_name])
            return cursor.fetchone()

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
    # print(data_points)
    # print(chrom_metadata)
    return chrom_metadata, data_points


def update_channel_data(result_id, system_name, data_points, target_column, use_orm=True):
    """
    Efficiently updates only the specific channel in time-series data without affecting other channels.
    Uses batch inserts/updates instead of row-by-row operations.
    """

    if use_orm:
        # ✅ **Batch Update with ORM**
        time_series_objects = [
            TimeSeriesData(
                result_id=result_id,
                system_name=system_name,
                time=row['time_rounded'],
                **{target_column: row['measurement']}
            )
            for _, row in data_points.iterrows()
        ]
        TimeSeriesData.objects.bulk_create(time_series_objects, ignore_conflicts=True)  # 🚀 Bulk insert

        print(f"✅ Bulk inserted/updated {len(time_series_objects)} rows for {target_column} (ORM)")

    else:
        # ✅ **Batch Update with Raw SQL**
        time_series_data = [
            (result_id, system_name, row['time_rounded'], row['measurement'])
            for _, row in data_points.iterrows()
        ]

        with connection.cursor() as cursor:
            cursor.executemany(
                f"""
                INSERT INTO time_series_data (result_id, system_name, time, {target_column})
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE {target_column} = VALUES({target_column});
                """,
                time_series_data
            )

        print(f"✅ Bulk inserted/updated {len(time_series_data)} rows for {target_column} (Raw SQL)")

    if target_column == 'channel_3':
        with connection.cursor() as cursor:
           # Calculate statistics
            cursor.execute("""
                        SELECT 
                            AVG(channel_1), 
                            MAX(channel_1), 
                            MIN(channel_1), 
                            VARIANCE(channel_1), 
                            STDDEV(channel_1),
                            MAX(time) - MIN(time)
                        FROM time_series_data WHERE result_id = %s;
                    """, [result_id])

            avg_pressure, max_pressure, min_pressure, pressure_variance, pressure_stddev, retention_time_range = cursor.fetchone()

            # Find time when max pressure occurred
            cursor.execute("""
                        SELECT time FROM time_series_data 
                        WHERE result_id = %s ORDER BY channel_1 DESC LIMIT 1;
                    """, [result_id])
            peak_pressure_time = cursor.fetchone()[0]

            # Update chrom_metadata with new statistics
            cursor.execute("""
                        UPDATE chrom_metadata 
                        SET average_pressure = %s, max_pressure = %s, min_pressure = %s, 
                            pressure_variance = %s, pressure_stddev = %s, 
                            retention_time_range = %s, peak_pressure_time = %s
                        WHERE result_id = %s;
                    """, [
                avg_pressure, max_pressure, min_pressure,
                pressure_variance, pressure_stddev,
                retention_time_range, peak_pressure_time, result_id
            ])

            print(f"Updated chrom_metadata with pressure stats for result_id {result_id}.")


def update_channel_data(result_id, system_name, data_points, target_column, use_orm=True):
    """
    Efficiently updates only the specific channel in time-series data without affecting other channels.
    Uses batch inserts/updates instead of row-by-row operations.
    """

    if use_orm:
        # ✅ **Batch Update with ORM**
        time_series_objects = [
            TimeSeriesData(
                result_id=result_id,
                system_name=system_name,
                time=row['time_rounded'],
                **{target_column: row['measurement']}
            )
            for _, row in data_points.iterrows()
        ]
        TimeSeriesData.objects.bulk_create(time_series_objects, ignore_conflicts=True)  # 🚀 Bulk insert

        print(f"✅ Bulk inserted/updated {len(time_series_objects)} rows for {target_column} (ORM)")

    elif not use_orm:
        # ✅ **Batch Update with Raw SQL**
        time_series_data = [
            (result_id, system_name, row['time_rounded'], row['measurement'])
            for _, row in data_points.iterrows()
        ]

        with connection.cursor() as cursor:
            cursor.executemany(
                f"""
                INSERT INTO time_series_data (result_id, system_name, time, {target_column})
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE {target_column} = VALUES({target_column});
                """,
                time_series_data
            )

        print(f"✅ Bulk inserted/updated {len(time_series_data)} rows for {target_column} (Raw SQL)")

    elif target_column == 'channel_3':
        with connection.cursor() as cursor:
           # Calculate statistics
            cursor.execute("""
                        SELECT 
                            AVG(channel_1), 
                            MAX(channel_1), 
                            MIN(channel_1), 
                            VARIANCE(channel_1), 
                            STDDEV(channel_1),
                            MAX(time) - MIN(time)
                        FROM time_series_data WHERE result_id = %s;
                    """, [result_id])

            avg_pressure, max_pressure, min_pressure, pressure_variance, pressure_stddev, retention_time_range = cursor.fetchone()

            # Find time when max pressure occurred
            cursor.execute("""
                        SELECT time FROM time_series_data 
                        WHERE result_id = %s ORDER BY channel_1 DESC LIMIT 1;
                    """, [result_id])
            peak_pressure_time = cursor.fetchone()[0]

            # Update chrom_metadata with new statistics
            cursor.execute("""
                        UPDATE chrom_metadata 
                        SET average_pressure = %s, max_pressure = %s, min_pressure = %s, 
                            pressure_variance = %s, pressure_stddev = %s, 
                            retention_time_range = %s, peak_pressure_time = %s
                        WHERE result_id = %s;
                    """, [
                avg_pressure, max_pressure, min_pressure,
                pressure_variance, pressure_stddev,
                retention_time_range, peak_pressure_time, result_id
            ])

            print(f"Updated chrom_metadata with pressure stats for result_id {result_id}.")



def insert_into_database(chrom_metadata, data_points, use_orm=True):
    """ Inserts or updates metadata and time-series data into the database using ORM or raw SQL. """

    # ✅ Retrieve channel mappings from system_information
    channel_names = query_channels_by_system(chrom_metadata["system_name"], use_orm)
    if not channel_names:
        print(f"⚠️ System '{chrom_metadata['system_name']}' not found in system_information.")
        return

    # ✅ Map file channel name to database column
    file_channel_name = chrom_metadata.get('channel', '').strip().lower()
    channel_to_column = {
        f"{channel_names[0]}": "channel_1",
        f"{channel_names[1]}": "channel_2",
        f"{channel_names[2]}": "channel_3"
    }
    target_column = channel_to_column.get(file_channel_name)

    if not target_column:
        print(f"⚠️ Channel '{file_channel_name}' not recognized. Skipping insert.")
        return

    result_id = chrom_metadata["injection_id"]
    system_name = chrom_metadata["system_name"]

    print(f"🔹 Processing result_id {result_id}, system: {system_name}, channel: {file_channel_name}")

    if use_orm:
        # ✅ **Insert/Update ChromMetadata using ORM**
        ChromMetadata.objects.update_or_create(
            result_id=result_id,
            defaults={
                "system_name": system_name,
                "sample_name": chrom_metadata.get("samplename"),
                "sample_set_name": chrom_metadata.get("sample_set_name"),
                "sample_set_id": chrom_metadata.get("sample_set_id"),
                target_column: file_channel_name  # ✅ Only updates this column
            }
        )

    else:
        with connection.cursor() as cursor:
            # ✅ **Insert/Update ChromMetadata using Raw SQL**
            cursor.execute(
                f"""
                INSERT INTO chrom_metadata (result_id, system_name, sample_name, sample_set_name, sample_set_id, {target_column})
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE {target_column} = VALUES({target_column});
                """,
                (result_id, system_name, chrom_metadata.get("samplename"), chrom_metadata.get("sample_set_name"),
                 chrom_metadata.get("sample_set_id"), file_channel_name)
            )

    # ✅ **Batch Insert Time-Series Data**
    update_channel_data(result_id, system_name, data_points, target_column, use_orm)

    print(f"✅ Inserted/Updated data for result_id {result_id} using {'ORM' if use_orm else 'Raw SQL'}")


def process_files(directory, reported_folder, use_orm=False):
    """ Processes all ARW files and inserts data into MySQL using ORM or raw SQL. """

    # Ensure the Reported folder exists
    os.makedirs(reported_folder, exist_ok=True)

    # Get the list of .arw files
    files = [f for f in os.listdir(directory) if f.endswith(".arw")]
    if not files:
        print("⚠️ No .arw files found.")
        return

    # Process each file
    for filename in tqdm(files, desc="Processing Files", unit="file"):
        file_path = os.path.join(directory, filename)

        # Parse the file
        chrom_metadata, data_points = parse_arw_file(file_path)

        # Insert into the database
        insert_into_database(chrom_metadata, data_points, use_orm)

        # Move file to the reported folder
        shutil.move(file_path, os.path.join(reported_folder, filename))

    print("✅ Processing complete!")



# def insert_time_series_data(result_id, system_name, time, channel_1, channel_2=None, channel_3=None):
#     """
#     Inserts time-series data and updates the average pressure in chrom_metadata.
#     """
#     with connection.cursor() as cursor:
#         # Insert new time-series data
#         cursor.execute("""
#             INSERT INTO time_series_data (result_id, system_name, time, channel_1, channel_2, channel_3)
#             VALUES (%s, %s, %s, %s, %s, %s);
#         """, [result_id, system_name, time, channel_1, channel_2, channel_3])
#
#         # Calculate average pressure for this result_id
#         cursor.execute("""
#             SELECT AVG(channel_1) FROM time_series_data WHERE result_id = %s;
#         """, [result_id])
#         avg_pressure = cursor.fetchone()[0]
#
#         if avg_pressure is not None:
#             # Update chrom_metadata with the calculated average pressure
#             cursor.execute("""
#                 UPDATE chrom_metadata SET average_pressure = %s WHERE result_id = %s;
#             """, [avg_pressure, result_id])
#
#             print(f"Updated average_pressure {avg_pressure} for result_id {result_id} in chrom_metadata.")



