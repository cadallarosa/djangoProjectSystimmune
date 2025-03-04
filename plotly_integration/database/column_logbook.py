from django.db import connection


def populate_column_logbook():
    """
    Inserts existing column serial numbers from sample_metadata into empower_column_logbook
    and generates an integer ID for each unique serial number.
    """
    with connection.cursor() as cursor:
        # Find unique column serial numbers from sample_metadata
        cursor.execute(
            "SELECT DISTINCT column_serial_number FROM sample_metadata WHERE column_serial_number IS NOT NULL;")
        column_serials = cursor.fetchall()

        for serial_number in column_serials:
            column_serial = serial_number[0]

            # Check if it already exists in empower_column_logbook
            cursor.execute("SELECT id FROM empower_column_logbook WHERE column_serial_number = %s;", [column_serial])
            existing = cursor.fetchone()

            if not existing:
                # Insert a new record for this column
                cursor.execute(
                    "INSERT INTO empower_column_logbook (column_serial_number, column_name, total_injections) VALUES (%s, %s, 0);",
                    [column_serial, "Unknown Column"]  # Default column name for existing data
                )
                print(f"Inserted column {column_serial} into empower_column_logbook.")


populate_column_logbook()


def transfer_column_names():
    """
    Transfers column names from sample_metadata to empower_column_logbook.
    """
    with connection.cursor() as cursor:
        # Get distinct column serial numbers and associated column names from sample_metadata
        cursor.execute("""
            SELECT DISTINCT column_serial_number, column_name
            FROM sample_metadata
            WHERE column_serial_number IS NOT NULL AND column_name IS NOT NULL;
        """)
        columns = cursor.fetchall()

        for column_serial, column_name in columns:
            # Update the column name in empower_column_logbook
            cursor.execute("""
                UPDATE empower_column_logbook
                SET column_name = %s
                WHERE column_serial_number = %s;
            """, [column_name, column_serial])

            print(f"Updated column {column_serial} with name '{column_name}'.")


transfer_column_names()

from django.db import connection


def update_total_injections():
    """
    Updates total_injections in empower_column_logbook based on the number of times
    each column_serial_number appears in sample_metadata.
    """
    with connection.cursor() as cursor:
        # Count how many times each column serial number appears in sample_metadata
        cursor.execute("""
            SELECT column_serial_number, COUNT(*) AS injection_count
            FROM sample_metadata
            WHERE column_serial_number IS NOT NULL
            GROUP BY column_serial_number;
        """)
        column_usage_counts = cursor.fetchall()

        for column_serial, injection_count in column_usage_counts:
            # Update the total_injections in empower_column_logbook
            cursor.execute("""
                UPDATE empower_column_logbook
                SET total_injections = %s
                WHERE column_serial_number = %s;
            """, [injection_count, column_serial])

            print(f"Updated column {column_serial} with total_injections = {injection_count}.")


update_total_injections()


def insert_sample(result_id, system_name, sample_name, sample_set_id, column_serial):
    """
    Inserts a new sample into sample_metadata and updates total_injections in empower_column_logbook.
    """
    with connection.cursor() as cursor:
        # Ensure column exists and get its ID
        cursor.execute("SELECT id FROM empower_column_logbook WHERE column_serial_number = %s", [column_serial])
        row = cursor.fetchone()

        if row:
            column_id = row[0]
        else:
            # If column doesn't exist, insert it
            cursor.execute(
                "INSERT INTO empower_column_logbook (column_serial_number, column_name, total_injections) VALUES (%s, %s, 0)",
                [column_serial, "Unknown Column"]  # Default column name
            )
            column_id = cursor.lastrowid  # Get newly inserted column ID

        # Insert new sample into sample_metadata
        cursor.execute(
            "INSERT INTO sample_metadata (result_id, system_name, sample_name, sample_set_id, column_id) VALUES (%s, %s, %s, %s, %s)",
            [result_id, system_name, sample_name, sample_set_id, column_id]
        )

        # Increment total_injections in empower_column_logbook
        cursor.execute("UPDATE empower_column_logbook SET total_injections = total_injections + 1 WHERE id = %s", [column_id])

        print(f"Inserted sample {sample_name} (result_id: {result_id}) and updated column {column_serial} (id: {column_id}) with +1 injection.")

# Example Usage:
# insert_sample(101, "SystemA", "SampleX", 2001, "SN12345")


from django.db import connection

def backfill_missing_pressure_data():
    """
    Finds all result_ids in chrom_metadata with missing average_pressure,
    calculates statistics from time_series_data (channel_3), and updates chrom_metadata.
    """
    with connection.cursor() as cursor:
        # Step 1: Find result_ids with missing average_pressure
        cursor.execute("""
            SELECT result_id FROM chrom_metadata 
            WHERE average_pressure IS NULL;
        """)
        missing_result_ids = [row[0] for row in cursor.fetchall()]

        if not missing_result_ids:
            print("✅ No missing average_pressure values found. Database is up-to-date.")
            return

        print(f"⚡ Found {len(missing_result_ids)} result_ids missing average_pressure. Processing...")

        for result_id in missing_result_ids:
            print(f"🔄 Processing result_id: {result_id}")

            # Step 2: Calculate statistics using channel_3 from time_series_data
            cursor.execute("""
                SELECT 
                    AVG(channel_3), 
                    MAX(channel_3), 
                    MIN(channel_3), 
                    VARIANCE(channel_3), 
                    STDDEV(channel_3),
                    MAX(time) - MIN(time)
                FROM time_series_data WHERE result_id = %s;
            """, [result_id])

            stats = cursor.fetchone()

            if not stats or stats[0] is None:
                print(f"⚠ Warning: No time-series data found for result_id {result_id}. Skipping...")
                continue  # Skip if no data is found

            avg_pressure, max_pressure, min_pressure, pressure_variance, pressure_stddev, retention_time_range = stats

            # Step 3: Find peak pressure time
            cursor.execute("""
                SELECT time FROM time_series_data 
                WHERE result_id = %s ORDER BY channel_3 DESC LIMIT 1;
            """, [result_id])
            peak_pressure_time = cursor.fetchone()

            peak_pressure_time = peak_pressure_time[0] if peak_pressure_time else None

            # Step 4: Update chrom_metadata with calculated values
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

            print(f"✅ Updated chrom_metadata for result_id {result_id}")

    print("🚀 Backfill complete! All missing values have been updated.")

# Run the script
backfill_missing_pressure_data()




def assign_column_ids_to_samples():
    """
    Assigns the correct column_id to each record in sample_metadata
    based on the column_serial_number.
    """
    with connection.cursor() as cursor:
        # Get all sample_metadata records with a column_serial_number
        cursor.execute("""
            SELECT result_id, column_serial_number 
            FROM sample_metadata 
            WHERE column_serial_number IS NOT NULL;
        """)
        samples = cursor.fetchall()

        updated_count = 0

        for result_id, column_serial in samples:
            # Find the corresponding column_id from empower_column_logbook
            cursor.execute("""
                SELECT id FROM empower_column_logbook 
                WHERE column_serial_number = %s;
            """, [column_serial])
            column_row = cursor.fetchone()

            if column_row:
                column_id = column_row[0]

                # Update sample_metadata with the correct column_id
                cursor.execute("""
                    UPDATE sample_metadata 
                    SET column_id = %s 
                    WHERE result_id = %s;
                """, [column_id, result_id])

                updated_count += 1
                print(f"✅ Updated result_id {result_id}: Assigned column_id {column_id} (was serial {column_serial})")

        print(f"🚀 Finished updating {updated_count} samples with correct column_id.")

# Run the update function
assign_column_ids_to_samples()


from django.db import connection

def update_most_recent_injections():
    """
    Finds the most recent sample injection for each column_id in empower_column_logbook
    and updates the empower_column_logbook table.
    """
    with connection.cursor() as cursor:
        # Retrieve all column IDs from empower_column_logbook
        cursor.execute("SELECT id FROM empower_column_logbook;")
        column_ids = [row[0] for row in cursor.fetchall()]

        updated_count = 0

        for column_id in column_ids:
            # Get the most recent injection for this column_id
            cursor.execute("""
                SELECT result_id, sample_name, MAX(date_acquired)
                FROM sample_metadata
                WHERE column_id = %s
                GROUP BY result_id, sample_name
                ORDER BY MAX(date_acquired) DESC
                LIMIT 1;
            """, [column_id])

            result = cursor.fetchone()

            if result:
                result_id, sample_name, injection_timestamp = result

                # Update empower_column_logbook with the most recent injection
                cursor.execute("""
                    UPDATE empower_column_logbook
                    SET most_recent_injection_date = %s
                    WHERE id = %s;
                """, [injection_timestamp, column_id])

                updated_count += 1
                print(f"✅ Updated column_id {column_id}: Most recent injection on {injection_timestamp}")

        print(f"🚀 Finished updating {updated_count} columns with their most recent injection.")

# Run the function
update_most_recent_injections()
