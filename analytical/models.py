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

