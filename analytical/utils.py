import sqlite3
import pandas as pd
import matplotlib.pyplot as plt


# Database-related functions
def query_sample_metadata(conn, sample_name_range):
    cursor = conn.cursor()
    if '-' in sample_name_range:
        start, end = sample_name_range.split('-')
        cursor.execute("""
            SELECT result_id, sample_name 
            FROM sample_metadata 
            WHERE sample_name BETWEEN ? AND ?
        """, (start, end))
    else:
        cursor.execute("""
            SELECT result_id, sample_name 
            FROM sample_metadata 
            WHERE sample_name = ?
        """, (sample_name_range,))
    return cursor.fetchall()


def query_time_series_data(conn, result_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM time_series_data 
        WHERE result_id = ?
    """, (result_id,))
    data = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return pd.DataFrame(data, columns=columns)


def query_system_information(conn, system_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT channel_1, channel_2, channel_3 
        FROM system_information 
        WHERE system_name = ?
    """, (system_name,))
    return cursor.fetchone()


# Plotting function
def plot_time_series_data(conn, dataframes, mode="overlay", channel_plot_logic=None):
    """
    Plots time-series analytical based on channel boolean logic using actual channel names.

    Parameters:
    - conn: Database connection.
    - dataframes: List of dataframes containing time-series analytical.
    - mode: Plotting mode ("overlay" or "panel").
    - channel_plot_logic: Dictionary with generic channel names as keys and booleans as values.
      Example: {"Channel 1": True, "Channel 2": False, "Channel 3": True}
    """
    fig = plt.figure(figsize=(12, 6))

    # Relate generic channel names to the actual columns in the dataframe
    channel_mapping = {
        "Channel 1": "channel_1",
        "Channel 2": "channel_2",
        "Channel 3": "channel_3"
    }

    if mode == "overlay":
        for df in dataframes:
            sample_name = df["sample_name"].iloc[0]  # Get the sample name from the dataframe
            # Get the system name from the metadata (first row sample_name)
            system_name = df["system_name"].iloc[0]
            system_info = query_system_information(conn, system_name)
            if not system_info:
                print(f"Warning: No system information found for {system_name}. Skipping this sample.")
                continue

            # Relate channels to their respective column names
            channel_1, channel_2, channel_3 = system_info

            for generic_channel, plot in channel_plot_logic.items():
                if plot:  # If the channel is marked to plot, proceed
                    actual_column = channel_mapping.get(generic_channel)
                    if actual_column and actual_column in df.columns:
                        # Add sample name and channel to the legend
                        label = f"{sample_name} - {generic_channel}"
                        plt.plot(df["time"], df[actual_column], label=label)
                    else:
                        print(f"Warning: Column '{actual_column}' not found in the dataframe.")
        plt.legend()
        plt.title(f"Time Series Data")
        plt.xlabel("Time")
        plt.ylabel("Intensity")
        plt.grid()
    elif mode == "panel":
        fig, axs = plt.subplots(len(dataframes), 1, figsize=(12, 6 * len(dataframes)), sharex=True)
        for i, df in enumerate(dataframes):
            sample_name = df["sample_name"].iloc[0]
            system_name = df["system_name"].iloc[0]
            system_info = query_system_information(conn, system_name)
            if not system_info:
                print(f"Warning: No system information found for {system_name}. Skipping this sample.")
                continue

            channel_1, channel_2, channel_3 = system_info
            for generic_channel, plot in channel_plot_logic.items():
                if plot:  # If the channel is marked to plot, proceed
                    actual_column = channel_mapping.get(generic_channel)
                    if actual_column and actual_column in df.columns:
                        axs[i].plot(df["time"], df[actual_column], label=generic_channel)
                    else:
                        print(f"Warning: Column '{actual_column}' not found in the dataframe.")
            axs[i].legend()
            axs[i].set_title(f"Sample: {sample_name}")
            axs[i].set_xlabel("Time")
            axs[i].set_ylabel("Intensity")
            axs[i].grid()
    # plt.show()

    return fig


# Main workflow
def main_workflow(db_name, sample_name_range, mode="overlay", channel_plot_logic=None):
    """
    Main function to execute the workflow with the given database and sample name range.
    """
    # Establish database connection
    conn = sqlite3.connect(db_name)

    # Get sample metadata for the given sample name range
    samples = query_sample_metadata(conn, sample_name_range)

    if not samples:
        print(f"No samples found for the range: {sample_name_range}")
        conn.close()
        return

    # Fetch and process time series analytical for each sample
    dataframes = []
    for result_id, sample_name in samples:
        print(f"Processing time series for {sample_name} (Result ID: {result_id})")
        # Fetch time series analytical for this result_id
        df = query_time_series_data(conn, result_id)
        # Add sample name to the dataframe
        df["sample_name"] = sample_name
        # Fetch system_name from metadata
        cursor = conn.cursor()
        cursor.execute("SELECT system_name FROM sample_metadata WHERE result_id = ?", (result_id,))
        system_name = cursor.fetchone()[0]
        df["system_name"] = system_name
        dataframes.append(df)

    # Call the plot function with the dataframes and pass the database connection
    fig = plot_time_series_data(conn, dataframes, mode, channel_plot_logic)

    # Close the database connection
    conn.close()

    return fig

