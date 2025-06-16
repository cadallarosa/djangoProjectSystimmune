from plotly_integration.process_development.lims.cld_sample_manager.app import app
from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
from plotly_integration.process_development.lims.cld_sample_manager.layout.table_config import EDITABLE_FIELDS, FIELD_IDS, UP_SAMPLE_FIELDS
from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, LimsSecResult
from collections import defaultdict

#View Samples Tab
@app.callback(
    Output("sample-set-sample-table", "data"),
    Output("sample-set-subtabs", "value"),
    Output("selected-sample-set-fbs", "data"),
    Input("sample-set-table", "active_cell"),
    State("sample-set-table", "data"),
    prevent_initial_call=True
)
def populate_sample_set_samples(active_cell, table_data):
    if not active_cell:
        raise PreventUpdate

    row = table_data[active_cell["row"]]
    sample_ids = row.get("sample_ids", [])  # Already in FB### format
    sample_numbers = [int(sid.replace("FB", "")) for sid in sample_ids]

    samples = LimsUpstreamSamples.objects.filter(
        sample_number__in=sample_numbers,
        sample_type=2
    ).order_by("sample_number")

    result = []
    for s in samples:
        sample_row = {}
        for field in [f["id"] for f in UP_SAMPLE_FIELDS]:
            val = getattr(s, field, None)
            if field == "harvest_date" and val:
                sample_row[field] = val.strftime("%Y-%m-%d")
            else:
                sample_row[field] = val
        result.append(sample_row)

    return result, "sample-set-view-samples-tab", sample_ids