from ..app import app
from dash import Input, Output, State, callback, ctx
from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis
from ..utils.helper import calculate_recoveries
import dash
from ..layout.table_config import EDITABLE_FIELDS, FIELD_IDS

# View Samples Table
@app.callback(
    Output("view-sample-table", "data"),
    Output("update-up-view-status", "children"),
    Input("upstream-tabs", "value"),
    Input("update-up-view-btn", "n_clicks"),
    State("view-sample-table", "data"),
    prevent_initial_call=False
)
def load_or_update_view_samples(tab, n_clicks, table_data):
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    updated, errors = 0, 0

    # Only update if the button was clicked
    if triggered == "update-up-view-btn" and table_data:
        for row in table_data:
            try:
                update_data = {field: row.get(field) or None for field in EDITABLE_FIELDS}
                LimsUpstreamSamples.objects.filter(
                    sample_number=row["sample_number"], sample_type=2
                ).update(**update_data)
                updated += 1
            except Exception as e:
                print(f"Update failed for sample {row.get('sample_number')}: {e}")
                errors += 1

    # Always reload data, sorted by descending sample_number
    samples = LimsUpstreamSamples.objects.filter(sample_type=2).order_by("-sample_number")
    new_data = []
    for s in samples:
        fast_pro_a, a280 = calculate_recoveries(s)
        row = {}
        for field in FIELD_IDS:
            if field == "harvest_date":
                value = getattr(s, field, None)
                row[field] = value.strftime("%Y-%m-%d") if value else None
            elif field != "report_link":  # Avoid getattr for dynamic fields
                row[field] = getattr(s, field, None)

        row["fast_pro_a_recovery"] = fast_pro_a
        row["purification_recovery_a280"] = a280

        analysis = LimsSampleAnalysis.objects.filter(sample_id=f"FB{s.sample_number}").first()
        if analysis and analysis.sec_result and analysis.sec_result.report_id:
            report_id = analysis.sec_result.report_id
            row[
                "report_link"] = f'[🔗 SEC Report](/plotly_integration/dash-app/app/SecReportApp2/?report_id={report_id})'
        else:
            row["report_link"] = ""

        new_data.append(row)

    status_msg = f"✅ Updated: {updated} | ❌ Errors: {errors}" if triggered == "update-up-view-btn" else dash.no_update
    return new_data, status_msg

