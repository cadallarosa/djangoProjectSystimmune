from collections import Counter
from datetime import datetime

import dash
from django.utils.timezone import is_aware, now
from plotly_integration.process_development.lims.cld_sample_manager.app import app
from dash import Input, Output, State, callback, ctx, no_update, callback_context
from plotly_integration.models import SampleMetadata, Report, LimsSampleAnalysis, LimsSecResult


@app.callback(
    Output("sec-report-sample-table", "data"),
    Output("sec-report-sample-table", "selected_rows"),
    Output("sec-expected-status", "children"),
    Output("sec-report-metadata", "children"),
    Input("selected-sample-set-fbs", "data"),
    prevent_initial_call=True
)
def populate_sec_report_table(fb_sample_ids):
    if not fb_sample_ids:
        return [], [], "", ""

    samples = list(SampleMetadata.objects.filter(sample_name__in=fb_sample_ids))
    sample_names = [s.sample_name for s in samples if s.sample_name]

    counts = Counter(sample_names)
    duplicates = {name for name, count in counts.items() if count > 1}
    found_set = set(sample_names)
    fb_set = set(fb_sample_ids)
    missing_samples = sorted(fb_set - found_set)

    data = []
    name_to_index = {}  # For selecting rows later
    for i, s in enumerate(samples):
        row = {
            "sample_name": s.sample_name,
            "result_id": s.result_id,
            "date_acquired": None,
            "column_name": s.column_name,
            "sample_set_name": s.sample_set_name,
            "duplicate": s.sample_name in duplicates
        }

        if s.date_acquired:
            dt = s.date_acquired
            if isinstance(dt, str):
                try:
                    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt = None
            if isinstance(dt, datetime) and is_aware(dt):
                dt = dt.replace(tzinfo=None)
            if isinstance(dt, datetime):
                row["date_acquired"] = dt.strftime("%m/%d/%Y %I:%M:%S %p")

        data.append(row)
        name_to_index[str(s.result_id)] = i

    # 🟡 Status message
    status_parts = []
    if missing_samples:
        status_parts.append(f"⚠️ Missing: {', '.join(missing_samples)}")
    if duplicates:
        status_parts.append(f"⚠️ Duplicate: {', '.join(sorted(duplicates))}")
    status_msg = " | ".join(status_parts) or f"✅ All {len(fb_sample_ids)} samples present"

    # 🔍 Metadata: Try to get existing report
    analysis_map = {
        s.sample_id: s for s in LimsSampleAnalysis.objects.filter(sample_id__in=fb_sample_ids)
    }
    results = LimsSecResult.objects.filter(sample_id__in=[a.sample_id for a in analysis_map.values()],
                                           report__isnull=False)
    report_ids = [r.report_id for r in results]

    selected_indices = list(range(len(data)))  # Default: select all
    report_name = ""
    report_date = ""
    metadata = ""

    if report_ids:
        most_common_report_id, _ = Counter(report_ids).most_common(1)[0]
        report = Report.objects.filter(report_id=most_common_report_id).first()
        if report:
            report_name = report.report_name
            report_date = f"📅 {report.date_created.strftime('%Y-%m-%d %H:%M')}"
            metadata = f"📄 Report: {report.report_name} (Project: {report.project_id})"
            selected_ids = report.selected_result_ids.split(",") if report.selected_result_ids else []
            selected_indices = [name_to_index[rid] for rid in selected_ids if rid in name_to_index]

    return data, selected_indices, status_msg, metadata

# @app.callback(
#     Output("view-sec-report", "style"),
#     Output("submit-sec-report", "n_clicks"),
#     Input("submit-sec-report", "n_clicks"),
#     Input("sample-set-subtabs", "value"),
#     State("sec-report-sample-table", "data"),
#     prevent_initial_call=True
# )
# def toggle_view_sec_report(n_clicks, active_tab, table_data):
#     # 🛠 FIX: Use callback_context only inside function
#     ctx = callback_context
#     trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""
#
#     if trigger_id == "submit-sec-report" and n_clicks:
#         return {"display": "inline-block"}, 0
#
#     if trigger_id == "sample-set-subtabs" and table_data:
#         sample_ids = [row.get("sample_name") for row in table_data if row.get("sample_name")]
#         if not sample_ids:
#             return {"display": "none"}, no_update
#
#         linked = LimsSecResult.objects.filter(sample_id__in=sample_ids, report__isnull=False).exists()
#         return ({"display": "inline-block"} if linked else {"display": "none"}), no_update
#
#     return no_update, no_update


@app.callback(
    Output("sec-report-status", "children"),
    Input("submit-sec-report", "n_clicks"),
    State("sec-report-sample-table", "data"),
    State("sec-report-sample-table", "selected_rows"),
    prevent_initial_call=True
)
def submit_sec_report(n_clicks, table_data, selected_rows):
    if not selected_rows or not table_data:
        return "⚠️ No rows selected."

    selected = [table_data[i] for i in selected_rows]
    sample_names = [row["sample_name"] for row in selected if row.get("sample_name")]
    result_ids = [str(row["result_id"]) for row in selected if row.get("result_id")]

    if not sample_names or not result_ids:
        return "⚠️ Invalid sample data."

    # Lookup sample analysis records
    analysis_map = {
        s.sample_id: s for s in LimsSampleAnalysis.objects.filter(sample_id__in=sample_names)
    }

    # Find existing report from LimsSecResult
    sec_results = LimsSecResult.objects.filter(sample_id__in=[a.sample_id for a in analysis_map.values()],
                                               report__isnull=False)

    report_ids = [r.report_id for r in sec_results]
    # Extract and sort FB sample names
    fb_names = sorted([name for name in sample_names if name.startswith("FB")])
    fb_start = fb_names[0] if fb_names else "FB0000"
    fb_end = fb_names[-1] if fb_names else "FB0000"

    timestamp = now()

    # Extract most common project name from SampleMetadata
    # Extract project IDs
    projects = [s.project_id for s in analysis_map.values() if s.project_id]
    project = Counter(projects).most_common(1)[0][0] if projects else "UNKNOWN"

    # Build report name
    report_name = f"{timestamp.strftime('%Y%m%d')}_{fb_start}_{fb_end}".replace(" ", "_")

    if report_ids:
        # Use most common report ID among selected samples
        most_common_report_id, _ = Counter(report_ids).most_common(1)[0]
        report = Report.objects.get(report_id=most_common_report_id)
        report.report_name = report_name
        report.project_id = project
        report.selected_samples = ",".join(sample_names)
        report.selected_result_ids = ",".join(result_ids)
        report.comments = "Updated from SEC report submission UI"
        report.save()
        is_new = False
    else:
        # Create new report

        report = Report.objects.create(
            report_name=report_name,
            project_id=project,
            user_id="system",
            comments="Auto-generated SEC report",
            selected_samples=",".join(sample_names),
            selected_result_ids=",".join(result_ids),
            date_created=timestamp,
            analysis_type=1,
            sample_type="FB",
            department=1
        )
        is_new = True

    # Link samples to the report
    created_or_updated = 0
    for s_name in sample_names:
        analysis = analysis_map.get(s_name)
        if not analysis:
            continue

        sec_result, _ = LimsSecResult.objects.get_or_create(sample_id=analysis)
        sec_result.report = report
        sec_result.save()
        created_or_updated += 1

    action = "Created" if is_new else "Updated"
    return f"✅ {action} SEC report '{report.report_name}' and linked {created_or_updated} samples."


@app.callback(
    [Output("sec-report-redirect", "href"),
     Output("view-sec-report", "n_clicks")],  # Reset button clicks
    Input("view-sec-report", "n_clicks"),
    State("view-sec-report", "n_clicks_timestamp"),
    State("selected-sample-set-fbs", "data"),
    prevent_initial_call=True
)
def redirect_to_report_by_sample_set(n_clicks, click_ts, fb_sample_ids):
    if not n_clicks or not click_ts or not fb_sample_ids:
        return no_update, no_update

    # Query LimsSampleAnalysis and LimsSecResult
    sample_map = {
        s.sample_id: s for s in LimsSampleAnalysis.objects.filter(sample_id__in=fb_sample_ids)
    }

    results = LimsSecResult.objects.filter(sample_id__in=sample_map.values(), report__isnull=False)
    report_ids = [r.report_id for r in results]

    if not report_ids:
        return no_update, no_update

    # Pick most common
    most_common_report_id, _ = Counter(report_ids).most_common(1)[0]

    redirect_url = f"/plotly_integration/dash-app/app/SecReportApp2/?hide_report_tab=true&report_id={most_common_report_id}"

    return redirect_url, 0  # Reset n_clicks to 0


@app.callback(
    Output("view-sec-report-container", "style"),
    Input("sample-set-dropdown", "value")  # replace with your actual Input
)
def toggle_report_button(sample_set):
    from plotly_integration.models import Report

    if not sample_set:
        return {"display": "none"}

    linked = Report.objects.filter(selected_samples__icontains=sample_set).exists()

    return {"display": "block"} if linked else {"display": "none"}
