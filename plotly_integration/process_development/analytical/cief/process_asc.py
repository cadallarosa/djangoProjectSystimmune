import os
import shutil
import hashlib
import pandas as pd
from datetime import datetime
from plotly_integration.models import CIEFTimeSeries, CIEFMetadata

def parse_asc_file(file_path):
    """
    Parse .asc file with vertical channel blocks based on 'Total Data Points' metadata.
    Each channel's data is stacked vertically (ch1, ch2, ch3).
    """
    import pandas as pd

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    metadata = {}
    data_lines = []
    for line in lines:
        if ':' in line:
            parts = line.strip().split(':', 1)
            key = parts[0].strip()
            value_str = parts[1].strip()

            # Detect delimiter (comma or tab)
            if ',' in value_str:
                rest = value_str.split(',')
            else:
                rest = value_str.split('\t')

            value = [v.strip() for v in rest if v.strip()]
            metadata[key] = value
        else:
            data_lines.append(line.strip())

    # Parse numeric values from data lines
    numeric_values = []
    for line in data_lines:
        try:
            numeric_values.append(float(line))
        except ValueError:
            continue

    # Get number of channels and points per channel
    try:
        num_channels = int(metadata.get('Maxchannels', ['3'])[0])
        points_per_channel = int(metadata.get('Total Data Points', ['0'])[0])  # <-- from metadata
        sampling_rate = float(metadata.get('Sampling Rate', ['2'])[0])
    except Exception as e:
        raise ValueError(f"Failed to parse required metadata fields: {e}")

    expected_length = num_channels * points_per_channel
    if len(numeric_values) < expected_length:
        raise ValueError(f"Expected {expected_length} values, found {len(numeric_values)}")

    # Slice vertically
    ch1 = numeric_values[0:points_per_channel]
    ch2 = numeric_values[points_per_channel:2*points_per_channel]
    ch3 = numeric_values[2*points_per_channel:3*points_per_channel]

    # Time vector in minutes
    time_step_min = (1 / sampling_rate) / 60
    time = pd.Series(range(points_per_channel)) * time_step_min

    # Build DataFrame
    df = pd.DataFrame({
        'time_min': time,
        'channel_1': ch1,
        'channel_2': ch2,
        'channel_3': ch3
    })
    print(df)

    return metadata, df


def generate_sample_set_id(sample_set_name):
    return int(hashlib.sha1(sample_set_name.encode('utf-8')).hexdigest(), 16) % (10**10)


def save_asc_to_db(file_path):
    metadata_dict, timeseries_df = parse_asc_file(file_path)

    # Extract folder name as sample set
    data_file_path = metadata_dict.get('Data File', [''])[0]
    sample_set_name = os.path.basename(os.path.dirname(data_file_path))
    sample_set_id = generate_sample_set_id(sample_set_name)

    # Fix here
    sample_id_full = metadata_dict.get('Sample ID', ['Unknown'])[0]
    parts = sample_id_full.split(' ', 1)
    sample_prefix = parts[0] if parts else 'Unknown'
    sample_id_clean = parts[1] if len(parts) > 1 else sample_id_full

    # Fix acquisition datetime
    acq_dt_str = metadata_dict.get('Acquisition Date and Time', [''])[0]
    try:
        acquisition_datetime = datetime.strptime(acq_dt_str, '%m/%d/%Y %I:%M:%S %p')
    except Exception:
        acquisition_datetime = None

    #✅ Skip if alreadyimported
    if CIEFMetadata.objects.filter(sample_id_full=sample_id_full, sample_set_id=sample_set_id).exists():
        print(f"⏭️ Skipping duplicate import for: {sample_id_full} ({sample_set_name})")
        return

    metadata = CIEFMetadata.objects.create(
        original_file_name=os.path.basename(file_path),
        sample_id_full=sample_id_full,
        sample_id_clean=sample_id_clean,
        sample_prefix=sample_prefix,
        data_file_path=metadata_dict.get('Data File', [''])[0],
        method_path=metadata_dict.get('Method', [''])[0],
        user_name=metadata_dict.get('User Name', [''])[0],
        acquisition_datetime=acquisition_datetime,
        sampling_rate=float(metadata_dict.get('Sampling Rate', ['2'])[0]),
        total_data_points=int(metadata_dict.get('Total Data Points', ['0'])[0]),
        x_axis_title=', '.join(metadata_dict.get('X Axis Title', [])),
        y_axis_title=', '.join(metadata_dict.get('Y Axis Title', [])),
        x_axis_multiplier=float(metadata_dict.get('X Axis Multiplier', ['1'])[0]),
        y_axis_multiplier=float(metadata_dict.get('Y Axis Multiplier', ['1'])[0]),
        sample_set_name=sample_set_name,
        sample_set_id=sample_set_id
    )

    # Bulk insert timeseries
    timeseries_objects = [
        CIEFTimeSeries(
            metadata=metadata,
            time_min=row['time_min'],
            channel_1=row['channel_1'],
            channel_2=row['channel_2'],
            channel_3=row['channel_3']
        )
        for _, row in timeseries_df.iterrows()
    ]

    CIEFTimeSeries.objects.bulk_create(timeseries_objects)

    return metadata.id


def move_file_to_processed(file_path, processed_folder):
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)
    shutil.move(file_path, os.path.join(processed_folder, os.path.basename(file_path)))


