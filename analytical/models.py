from django.db import models
from django.db import models
import sqlite3
import re


class Project(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    @staticmethod
    def get_unique_names(db_name, table_name, column_name):
        # Connect to the SQLite database
        conn = sqlite3.connect(db_name)

        # Create a cursor object
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name}")

        # Fetch all unique names
        unique_names = cursor.fetchall()

        # Close the connection to the database
        conn.close()

        # Convert the list of tuples into a list of strings
        unique_names = [name[0] for name in unique_names if name is not None]

        def get_sort_key(a):
            if a is None:
                return 0
            num = re.findall(r'\d+', a)  # find all groups of numbers in the name
            return int(num[0]) if num else 0

        unique_names = sorted(unique_names, key=get_sort_key)

        return unique_names


class Sample(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    @staticmethod
    def get_sample_names_by_project(db_name, project_name):
        # Connect to the SQLite database
        conn = sqlite3.connect(db_name)

        # Create a cursor object
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(f"SELECT sample_name FROM project_id WHERE project_name = ?",
                       (project_name,))

        # Fetch all unique names
        sample_names = cursor.fetchall()

        # Close the connection to the database
        conn.close()

        # Convert the list of tuples into a list of strings
        sample_names = [name[0] for name in sample_names]

        return sample_names




from django.db import models

class SampleMetadata(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    result_id = models.IntegerField()
    system_name = models.TextField()
    project_name = models.TextField(null=True, blank=True)
    sample_prefix = models.TextField(null=True, blank=True)
    sample_number = models.IntegerField(null=True, blank=True)
    sample_suffix = models.TextField(null=True, blank=True)
    sample_type = models.TextField(null=True, blank=True)
    sample_name = models.TextField(null=True, blank=True)
    sample_set_id = models.IntegerField(null=True, blank=True)
    sample_set_name = models.TextField(null=True, blank=True)
    date_acquired = models.DateField(null=True, blank=True)
    acquired_by = models.TextField(null=True, blank=True)
    run_time = models.FloatField(null=True, blank=True)
    processing_method = models.TextField(null=True, blank=True)
    processed_channel_description = models.TextField(null=True, blank=True)
    injection_volume = models.FloatField(null=True, blank=True)
    injection_id = models.IntegerField(null=True, blank=True)
    column_name = models.TextField(null=True, blank=True)
    column_serial_number = models.TextField(null=True, blank=True)
    instrument_method_id = models.IntegerField(null=True, blank=True)
    instrument_method_name = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'sample_metadata'
        managed = False
        unique_together = ('result_id', 'system_name')


class PeakResults(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    channel_name = models.TextField(null=True, blank=True)
    peak_name = models.TextField(null=True, blank=True)
    peak_retention_time = models.FloatField(null=True, blank=True)
    peak_start_time = models.FloatField(null=True, blank=True)
    peak_end_time = models.FloatField(null=True, blank=True)
    area = models.IntegerField(null=True, blank=True)
    percent_area = models.FloatField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    asym_at_10 = models.FloatField(null=True, blank=True)
    plate_count = models.FloatField(null=True, blank=True)
    res_hh = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'peak_results'
        managed = False
        unique_together = ('result_id', 'peak_retention_time')


class ChromMetadata(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.TextField()
    sample_name = models.TextField(null=True, blank=True)
    sample_set_name = models.TextField(null=True, blank=True)
    sample_set_id = models.IntegerField(null=True, blank=True)
    channel_1 = models.TextField(null=True, blank=True)
    channel_2 = models.TextField(null=True, blank=True)
    channel_3 = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'chrom_metadata'
        managed = False
        unique_together = ('result_id', 'system_name')


class TimeSeriesData(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.TextField()
    time = models.FloatField()
    channel_1 = models.FloatField(null=True, blank=True)
    channel_2 = models.FloatField(null=True, blank=True)
    channel_3 = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'time_series_data'
        managed = False
        unique_together = ('result_id', 'time')


class SystemInformation(models.Model):
    system_name = models.TextField(primary_key=True)
    channel_1 = models.TextField(null=True, blank=True)
    channel_2 = models.TextField(null=True, blank=True)
    channel_3 = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'system_information'
        managed = False


class ProjectID(models.Model):
    project_name = models.TextField(null=True, blank=True)
    sip_number = models.TextField(null=True, blank=True)
    clone_id = models.TextField(null=True, blank=True)
    sample_name = models.TextField(primary_key=True)
    description = models.TextField(null=True, blank=True)
    analyst = models.TextField(null=True, blank=True)
    harvest_date = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'project_id'
        managed = False


class Report(models.Model):
    report_id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    report_name = models.TextField(null=True, blank=True)
    project_id = models.TextField(null=True, blank=True)
    analysis_type = models.TextField(null=True, blank=True)
    sample_type = models.TextField(null=True, blank=True)
    selected_samples = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    user_id = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'report'
        managed = False


class Users(models.Model):
    user_id = models.IntegerField()
    user_name = models.TextField(primary_key=True)
    user_initials = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'users'
        managed = False


class Method(models.Model):
    method_id = models.AutoField(primary_key=True)
    method_type = models.IntegerField(null=True, blank=True)
    new_column_1 = models.IntegerField(null=True, blank=True)
    new_column_2 = models.IntegerField(null=True, blank=True)
    new_column_3 = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'method'
        managed = False


class ReportInstance(models.Model):
    report_instance_id = models.AutoField(primary_key=True)
    exclusions = models.TextField(null=True, blank=True)
    report_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'report_instance'
        managed = False


class Results(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.TextField(null=True, blank=True)
    project_name = models.IntegerField(null=True, blank=True)
    sample_set_id = models.IntegerField(null=True, blank=True)
    sample_set_name = models.TextField(null=True, blank=True)
    acquired_by = models.TextField(null=True, blank=True)
    column_serial_number = models.TextField(null=True, blank=True)
    new_column = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'results'
        managed = False


