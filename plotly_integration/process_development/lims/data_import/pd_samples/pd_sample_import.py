import os
import django
import pandas as pd
from datetime import datetime

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject.settings")
django.setup()

# Now import Django models
from plotly_integration.models import LimsSampleAnalysis

# Load Excel
file_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\lims\data_import\pd_samples\PD Samples.xlsx"
df = pd.read_excel(file_path)

# Clean and rename
df.columns = df.columns.str.strip()
df = df.rename(columns={
    "PD#": "sample_id",
    "Description + Volume": "description",
    "A280 date": "sample_date",
    "mg/ml": "a280_result"
})

# Convert types
df["sample_id"] = df["sample_id"].apply(lambda x: f"PD{int(x)}")  # 🔧 Corrected syntax
df["sample_date"] = pd.to_datetime(df["sample_date"], errors="coerce")

# Insert or update samples
created = 0
for _, row in df.iterrows():
    row = row.where(pd.notnull(row), None)  # Replace NaN with None

    # Skip rows with missing or empty description
    if not row.get("description"):
        continue

    obj, is_created = LimsSampleAnalysis.objects.update_or_create(
        sample_id=row["sample_id"],
        defaults={
            "description": row.get("description", ""),
            "sample_date": row.get("sample_date"),
            "a280_result": row.get("a280_result")
        }
    )
    created += 1 if is_created else 0

print(f"✅ Imported {len(df)} rows — {created} created, {len(df)-created} updated")
