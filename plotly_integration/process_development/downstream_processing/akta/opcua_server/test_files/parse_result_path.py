from plotly_integration.models import AktaResult
for result in AktaResult.objects.all():
    try:
        path_parts = result.result_path.split('/')
        result.report_name = path_parts[-2] if len(path_parts) >= 2 else None
        result.save(update_fields=["report_name"])
    except Exception as e:
        print(f"Error with {result.result_id}: {e}")