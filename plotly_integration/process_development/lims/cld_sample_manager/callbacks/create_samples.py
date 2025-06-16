from dash.exceptions import PreventUpdate

from ..app import app
from dash import Input, Output, State, callback, exceptions
from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, LimsProjectInformation
import dash

# Sample Creation
@app.callback(
    Output("up-project-dropdown", "options"),
    Input("upstream-tabs", "value"),
    prevent_initial_call=False
)
def populate_project_dropdown(tab):
    if tab != "create-tab":
        raise dash.exceptions.PreventUpdate

    project_qs = LimsProjectInformation.objects.all().order_by("protein", "molecule_type")

    options = [
        {
            "label": f"{p.protein} - {p.molecule_type}",
            "value": f"{p.protein}"
        }
        for p in project_qs if p.protein and p.molecule_type
    ]

    return options


@app.callback(
    Output("up-sample-table", "data"),
    Input("add-up-row", "n_clicks_timestamp"),
    Input("clear-up-table", "n_clicks_timestamp"),
    State("up-sample-table", "data"),
    prevent_initial_call=True
)
def modify_sample_table(add_ts, clear_ts, current_data):
    from plotly_integration.models import LimsUpstreamSamples
    from django.db.models import Max

    if current_data is None:
        current_data = []

    timestamps = {
        "add": add_ts or 0,
        "clear": clear_ts or 0,
    }
    latest_action = max(timestamps, key=timestamps.get)

    if latest_action == "clear":
        return []

    if latest_action == "add":
        db_max = LimsUpstreamSamples.objects.filter(sample_type=2).aggregate(Max("sample_number"))
        max_sample_number = db_max["sample_number__max"] or 0

        # Check in-memory data
        current_numbers = [
            int(row["sample_number"]) for row in current_data
            if str(row.get("sample_number")).isdigit()
        ]
        if current_numbers:
            max_sample_number = max(max_sample_number, max(current_numbers))

        next_sample_number = max_sample_number + 1

        current_data.append({
            "sample_number": next_sample_number,
            # "project": "",
            # "vessel_type": "",
            # "experiment_number": "",
            # "sip_number": "",
            # "unifi_number": "",
            # "development_stage": "",
            # "analyst": "",
            "cell_line": "",
            # "culture_duration": "",
            # "description": "",
            "harvest_date": "",
            "hf_octet_titer": "",
            "pro_aqa_hf_titer": "",
            "pro_aqa_e_titer": "",
            "proa_eluate_a280_conc": "",
            "hccf_loading_volume": "",
            "proa_eluate_volume": "",
            # "fast_pro_a_recovery": "",
            # "purification_recovery_a280": "",
            "note": ""
        })

        return current_data

    raise PreventUpdate


@app.callback(
    Output("save-up-status", "children"),
    Input("save-up-table", "n_clicks_timestamp"),
    State("up-sample-table", "data"),
    State("up-project-dropdown", "value"),
    State("up-vessel-type", "value"),
    State("cld-dev-stage", "value"),
    State("cld-analyst", "value"),
    State("sip-number", "value"),
    State("unifi-number", "value"),

    prevent_initial_call=True
)
def save_up_samples(save_up_ts, table_data, project, vessel_type, dev_stage, analyst, sip_number, unifi_number):
    from plotly_integration.models import LimsUpstreamSamples
    # print(project, vessel_type, dev_stage, analyst, sip_number, unifi_number)
    if not table_data:
        return "❌ No data to save."
    if not project or not vessel_type:
        return "⚠️ Please fill in Project and Vessel Type."

    print(f"💾 Saving UP samples for project '{project}' | vessel: {vessel_type}")

    created, skipped, errors = 0, 0, 0

    for row in table_data:
        try:
            sample_number = row.get("sample_number")
            if not sample_number:
                skipped += 1
                continue

            _, created_flag = LimsUpstreamSamples.objects.update_or_create(
                sample_number=sample_number,
                sample_type=2,
                defaults={
                    "project": project,
                    "vessel_type": vessel_type,
                    "sip_number": sip_number,
                    "unifi_number": unifi_number,
                    "development_stage": dev_stage,
                    "analyst": analyst,
                    "cell_line": row.get("cell_line") or "",
                    "harvest_date": row.get("harvest_date") or None,
                    "hf_octet_titer": row.get("hf_octet_titer") or None,
                    "pro_aqa_hf_titer": row.get("pro_aqa_hf_titer") or None,
                    "pro_aqa_e_titer": row.get("pro_aqa_e_titer") or None,
                    "proa_eluate_a280_conc": row.get("proa_eluate_a280_conc") or None,
                    "hccf_loading_volume": row.get("hccf_loading_volume") or None,
                    "proa_eluate_volume": row.get("proa_eluate_volume") or None,
                    "note": row.get("note") or "",
                }
            )

            LimsSampleAnalysis.objects.update_or_create(
                sample_id=f'FB{row["sample_number"]}',
                sample_type=2,
                defaults={
                    "sample_date": row.get("harvest_date") or None,
                    "project_id": project,
                    "description": row.get("description", ""),
                    "notes": row.get("note", ""),
                    "dn": None,
                    "a280_result": None
                }
            )

            created += 1 if created_flag else 0

        except Exception as e:
            print(f"❌ Error saving sample {row.get('sample_number')}: {e}")
            errors += 1

    return f"✅ Created/Updated: {created} | Skipped: {skipped} | Errors: {errors}"