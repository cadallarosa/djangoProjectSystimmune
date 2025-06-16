from plotly_integration.process_development.lims.cld_sample_manager.app import app
from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
from plotly_integration.process_development.lims.cld_sample_manager.layout.table_config import EDITABLE_FIELDS, FIELD_IDS, UP_SAMPLE_FIELDS
from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, LimsSecResult
from collections import defaultdict

# View Sample Sets Tab Logic
@app.callback(
    Output("sample-set-table", "data"),
    Output("sample-set-table-status", "children"),
    Input("upstream-tabs", "value"),
    prevent_initial_call=False
)
def load_sample_sets(tab):
    if tab != "sample-sets-tab":
        raise PreventUpdate

    from collections import defaultdict
    from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, LimsSecResult

    fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2)
    grouped = defaultdict(list)
    for s in fb_samples:
        key = (s.project, s.sip_number, s.development_stage)
        grouped[key].append(s.sample_number)

    all_sample_ids = [f"FB{n}" for s in fb_samples for n in [s.sample_number]]
    analysis_map = {
        sa.sample_id: sa for sa in LimsSampleAnalysis.objects.filter(sample_id__in=all_sample_ids)
    }
    sec_result_ids = set(
        sr.sample_id_id for sr in LimsSecResult.objects.filter(sample_id__in=analysis_map.keys())
    )

    table_data = []
    for (project, sip, dev_stage), sample_nums in grouped.items():
        if not sample_nums:
            continue

        sorted_nums = sorted(sample_nums)
        sample_ids = [f"FB{n}" for n in sorted_nums]
        sample_range = f"FB{sorted_nums[0]} to FB{sorted_nums[-1]}"

        num_with_sec = sum(1 for sid in sample_ids if sid in sec_result_ids)
        all_have_sec = num_with_sec == len(sample_ids)

        if all_have_sec:
            view_link = "[🔬 View SEC](/plotly_integration/dash-app/app/SecReportApp2/?report_id=1)"
        else:
            view_link = "⚠️ [🔬 View SEC](/plotly_integration/dash-app/app/SecReportApp2/?report_id=1)"

        table_data.append({
            "project": project or "",
            "sip": sip or "",
            "development_stage": dev_stage or "",
            "range": sample_range,
            "count": len(sample_ids),
            "view_sec_link": view_link,
            "view_sec": "▶️ View SEC",
            "sample_ids": sample_ids
        })

    return table_data, f"🔄 Loaded {len(table_data)} FB sample sets"


# @app.callback(
#     Output("report-update-status", "children"),
#     Input("sample-set-table", "active_cell"),
#     State("sample-set-table", "data"),
#     prevent_initial_call=True
# )
# def update_temp_report_id(active_cell, table_data):
#     from plotly_integration.models import Report, LimsSecResult
#     from collections import Counter
#     print(active_cell)
#     if not active_cell:
#         raise PreventUpdate
#
#     row = table_data[active_cell["row"]]
#     sample_ids = row.get("sample_ids", [])
#     sample_set_str = ",".join(sample_ids)
#
#     # Step 1: Fetch SEC results for the selected samples
#     sec_results = LimsSecResult.objects.filter(sample_id__sample_id__in=sample_ids)
#
#     # Step 2: Count associated report_ids
#     report_id_counts = Counter()
#     for result in sec_results:
#         if result.report_id:
#             report_id_counts[result.report_id] += 1
#
#     # Step 3: Determine most common report_id
#     most_common_report_id = None
#     if report_id_counts:
#         most_common_report_id, _ = report_id_counts.most_common(1)[0]
#
#     # Step 4: Pull settings from best-matching report
#     if most_common_report_id:
#         try:
#             source_report = Report.objects.get(report_id=most_common_report_id)
#             selected_result_ids = source_report.selected_result_ids or ""
#             comments = source_report.comments or ""
#             plot_settings = source_report.plot_settings if hasattr(source_report, "plot_settings") else None
#         except Report.DoesNotExist:
#             selected_result_ids = ""
#             comments = ""
#             plot_settings = None
#     else:
#         selected_result_ids = ""
#         comments = ""
#         plot_settings = None
#
#     # Step 5: Overwrite report ID 1
#     try:
#         report = Report.objects.get(report_id=1)
#         report.project_id = row.get("project")
#         report.analysis_type = 1
#         report.sample_type = "FB"
#         report.selected_samples = sample_set_str
#         report.selected_result_ids = selected_result_ids
#         report.comments = comments
#         report.plot_settings = plot_settings
#         report.save()
#     except Report.DoesNotExist:
#         return "❌ Report ID 1 not found."
#
#     return f"✅ Report ID 1 updated using Report ID {most_common_report_id or 'None'} with {len(sample_ids)} samples"


@app.callback(
    Output("sec-redirect", "href"),
    Output("report-update-status", "children"),
    Input("sample-set-table", "active_cell"),
    State("sample-set-table", "data"),
    prevent_initial_call=True
)
def create_temp_report_and_redirect(active_cell, table_data):
    from plotly_integration.models import Report, LimsSecResult
    from collections import Counter

    if not active_cell:
        raise PreventUpdate

    row = table_data[active_cell["row"]]
    clicked_col = active_cell["column_id"]
    if clicked_col != "view_sec":
        raise PreventUpdate

    sample_ids = row.get("sample_ids", [])
    sample_set_str = ",".join(sample_ids)

    # Find the most common report_id used in LimsSecResult for these samples
    sec_results = LimsSecResult.objects.filter(sample_id__sample_id__in=sample_ids)
    report_counts = Counter(r.report_id for r in sec_results if r.report_id)

    best_report_id = report_counts.most_common(1)[0][0] if report_counts else None

    # Get settings from the best report, if available
    selected_result_ids = comments = ""
    plot_settings = None
    if best_report_id:
        try:
            source = Report.objects.get(report_id=best_report_id)
            selected_result_ids = source.selected_result_ids or ""
            comments = source.comments or ""
            plot_settings = getattr(source, "plot_settings", None)
        except Report.DoesNotExist:
            pass

    report_fields = {
        "report_name": "__temp_fb_view_report__",
        "analysis_type": 1,
        "sample_type": "FB",
        "project_id": row.get("project"),
        "selected_samples": sample_set_str,
        "selected_result_ids": selected_result_ids,
        "comments": comments,
        "plot_settings": plot_settings,
    }

    # Update if report_id=1 exists
    updated = Report.objects.filter(report_id=1).update(**report_fields)

    # Otherwise, force-create it
    if updated == 0:
        temp_report = Report(report_id=1, **report_fields)
        temp_report.save(force_insert=True)

    return "/plotly_integration/dash-app/app/SecReportApp2/?report_id=1", \
           f"✅ Temp SEC report (ID 1) updated with {len(sample_ids)} samples"


