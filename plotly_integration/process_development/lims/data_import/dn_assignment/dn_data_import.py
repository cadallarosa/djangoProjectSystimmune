import os
import numpy as np
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject.settings")
django.setup()

import pandas as pd
from plotly_integration.models import LimsDnAssignment
from django.contrib.auth.models import User

def import_dn_assignments(file_path):
    df = pd.read_excel(file_path)

    df = df.replace({np.nan: None})  # 🧽 Replace NaN with None globally

    for _, row in df.iterrows():
        LimsDnAssignment.objects.update_or_create(
            dn=str(row["DN"]).strip(),
            defaults={
                "project_id": row.get("Project ID"),
                "study_name": row.get("Study name") or "",
                "experiment_purpose": row.get("Description of purpose") or "",
                "load_volume": float(row["Load volume"]) if row["Load volume"] is not None else None,
                "notes": row.get("Notes for any other data not conforming to notes in Unicorn"),
                "status": "Pending",
                "assigned_to": None,
                "created_by": None,
                "unit_operation": ""
            }
        )

import_dn_assignments(r'/plotly_integration/process_development/lims/data_import/DN_Assignment.xlsx')