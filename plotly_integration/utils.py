import pandas as pd
from django.db import transaction
from plotly_integration.models import Report, SampleMetadata  # Adjust based on your app

def convert_selected_samples_to_result_ids():
    reports = Report.objects.all()

    with transaction.atomic():  # Ensures all updates are committed together
        for report in reports:
            if not report.selected_samples:
                print(f"Skipping report '{report.report_name}' (No selected samples)")
                continue

            # Extract sample names from the report (assuming comma-separated format)
            sample_names = report.selected_samples.split(",")

            # Fetch corresponding result IDs
            data = []
            for sample_name in sample_names:
                sample_metadata = SampleMetadata.objects.filter(sample_name=sample_name).first()
                if sample_metadata:
                    data.append((sample_name, str(sample_metadata.result_id)))

            if not data:
                print(f"Skipping report '{report.report_name}' (No matching result IDs)")
                continue

            # ✅ Convert to DataFrame and sort by sample name
            df = pd.DataFrame(data, columns=["sample_name", "result_id"])
            df = df.sort_values(by="sample_name", ascending=True)

            # ✅ Extract sorted lists
            sorted_result_ids = df["result_id"].tolist()
            result_ids_str = ",".join(sorted_result_ids)

            # ✅ Use `update()` for bulk efficiency
            Report.objects.filter(report_id=report.report_id).update(selected_result_ids=result_ids_str)

            print(f"✅ Updated report '{report.report_name}' → Selected Result IDs: {result_ids_str}")

# Run the function
convert_selected_samples_to_result_ids()
