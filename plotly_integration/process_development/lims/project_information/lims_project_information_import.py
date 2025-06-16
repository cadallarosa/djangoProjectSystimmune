import os
import django
import numpy as np

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject.settings")
django.setup()

import pandas as pd
from datetime import datetime
from plotly_integration.models import LimsProjectInformation


# Clean float fields that might have comma-separated values
def safe_float(val):
    if isinstance(val, str) and "," in val:
        val = val.split(",")[0]  # take the first number
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

# Normalize boolean field
def safe_bool(val):
    if isinstance(val, str):
        val = val.strip().lower()
        if val in ["yes", "true", "1", "purified"]:
            return True
        elif val in ["no", "false", "0", "not purified"]:
            return False
    return bool(val) if pd.notnull(val) else None


# Load CSV
df = pd.read_csv("export.csv")
df.columns = df.columns.str.strip()

# Rename headers to match model fields
column_map = {
    "Protein": "protein",
    "Project": "project",
    "Project Description": "project_description",
    "Molecule Type": "molecule_type",
    "Description": "description",
    "Purifications": "purifications",
    "Plasmids": "plasmids",
    "Plasmid Description": "plasmid_description",
    "Tags": "tags",
    "Transfections": "transfections",
    "Titer [μg/mL]": "titer",
    "Protein Concentration [mg/mL]": "protein_concentration",
    "NanoDrop E1%": "nanodrop_e1",
    "Molecular Weight [Da]": "molecular_weight",
    "% POI": "percent_poi",
    "pI": "pi",
    "Latest Purification Date": "latest_purification_date",
    "Purified": "purified"
}
df = df.rename(columns=column_map)

# Convert date safely first
if "latest_purification_date" in df.columns:
    df["latest_purification_date"] = pd.to_datetime(df["latest_purification_date"], errors="coerce")

# Replace ALL NaN/NaT across the board
df = df.replace({np.nan: None, pd.NaT: None})

# Import records
for _, row in df.iterrows():
    data = row.drop(labels=["ID", "project"]).to_dict()

    # Clean float fields
    for float_field in ["titer", "protein_concentration", "nanodrop_e1", "molecular_weight", "percent_poi", "pi"]:
        if float_field in data:
            data[float_field] = safe_float(data[float_field])

    # Clean boolean field
    if "purified" in data:
        data["purified"] = safe_bool(data["purified"])

    obj, created = LimsProjectInformation.objects.update_or_create(
        project=row["protein"],
        defaults=data
    )
    print(f"{'🆕 Created' if created else '✏️ Updated'}: {obj.project}")