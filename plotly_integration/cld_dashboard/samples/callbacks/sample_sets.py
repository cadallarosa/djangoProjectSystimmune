# samples/callbacks/sample_sets.py
"""
Callbacks for sample sets management with SEC integration
"""

import re
from collections import defaultdict
from datetime import datetime
from django.db.models import Max
from dash import Input, Output, State, callback, ctx, no_update
import dash
from plotly_integration.models import (
    LimsUpstreamSamples, LimsSampleAnalysis, LimsSecResult,
    LimsProjectInformation
)
from ...shared.utils.url_helpers import build_action_buttons_markdown


def create_sample_sets_callbacks(app):
    """Create all callbacks for sample sets management"""

    @app.callback(
        Output("enhanced-sample-sets-table", "data"),
        Output("sample-sets-status", "children"),
        [Input("refresh-sample-sets", "n_clicks"),
         Input("url", "pathname")],
        prevent_initial_call=False
    )
    def load_sample_sets_with_sec_status(refresh_clicks, pathname):
        """Load sample sets with enhanced SEC status information"""
        if pathname not in ["/fb-samples/sets", "/sec/sample-sets"]:
            return [], ""

        try:
            data = get_sample_sets_with_sec_status()
            status = f"📊 Loaded {len(data)} sample sets"
            return data, status
        except Exception as e:
            return [], f"❌ Error loading sample sets: {str(e)}"

    @app.callback(
        Output("all-fb-samples-table", "data"),
        Output("all-samples-status", "children"),
        [Input("refresh-all-samples", "n_clicks"),
         Input("save-all-samples", "n_clicks"),
         Input("url", "pathname")],
        [State("all-fb-samples-table", "data")],
        prevent_initial_call=False
    )
    def load_or_update_all_samples(refresh_clicks, save_clicks, pathname, table_data):
        """Load or update all FB samples"""
        if pathname != "/fb-samples/view":
            return [], ""

        ctx_triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        # Handle save operation
        if ctx_triggered == "save-all-samples" and table_data:
            updated, errors = update_sample_data(table_data)
            status_msg = f"✅ Updated: {updated} samples | ❌ Errors: {errors}"
        else:
            status_msg = ""

        # Always reload data
        try:
            data = load_all_fb_samples_data()
            if not status_msg:
                status_msg = f"📊 Loaded {len(data)} FB samples"
            return data, status_msg
        except Exception as e:
            return [], f"❌ Error loading samples: {str(e)}"

    @app.callback(
        Output("create-project-dropdown", "options"),
        Input("url", "pathname"),
        prevent_initial_call=False
    )
    def populate_project_dropdown(pathname):
        """Populate project dropdown for sample creation"""
        if pathname != "/fb-samples/create":
            return []

        try:
            projects = LimsProjectInformation.objects.all().order_by("protein", "molecule_type")
            return [
                {
                    "label": f"{p.protein} - {p.molecule_type}",
                    "value": p.protein
                }
                for p in projects if p.protein and p.molecule_type
            ]
        except Exception as e:
            print(f"Error loading projects: {e}")
            return []

    @app.callback(
        Output("create-samples-table", "data"),
        [Input("add-sample-row", "n_clicks"),
         Input("clear-sample-table", "n_clicks")],
        [State("create-samples-table", "data")],
        prevent_initial_call=True
    )
    def modify_sample_creation_table(add_clicks, clear_clicks, current_data):
        """Add or clear rows in sample creation table"""
        if current_data is None:
            current_data = []

        ctx_triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        if ctx_triggered == "clear-sample-table":
            return []

        if ctx_triggered == "add-sample-row":
            # Get next sample number
            try:
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
                    "cell_line": "",
                    "harvest_date": "",
                    "hf_octet_titer": "",
                    "pro_aqa_hf_titer": "",
                    "pro_aqa_e_titer": "",
                    "proa_eluate_a280_conc": "",
                    "hccf_loading_volume": "",
                    "proa_eluate_volume": "",
                    "note": ""
                })

            except Exception as e:
                print(f"Error adding sample row: {e}")

        return current_data

    @app.callback(
        Output("create-samples-status", "children"),
        Input("save-new-samples", "n_clicks"),
        [State("create-samples-table", "data"),
         State("create-project-dropdown", "value"),
         State("create-vessel-type", "value"),
         State("create-dev-stage", "value"),
         State("create-analyst", "value"),
         State("create-sip-number", "value")],
        prevent_initial_call=True
    )
    def save_new_samples(n_clicks, table_data, project, vessel_type, dev_stage, analyst, sip_number):
        """Save new FB samples to database"""
        if not table_data:
            return "❌ No data to save."
        if not project or not vessel_type:
            return "⚠️ Please fill in Project and Vessel Type."

        try:
            created, skipped, errors = save_sample_data(
                table_data, project, vessel_type, dev_stage, analyst, sip_number
            )
            return f"✅ Created/Updated: {created} | Skipped: {skipped} | Errors: {errors}"
        except Exception as e:
            return f"❌ Error saving samples: {str(e)}"


def get_sample_sets_with_sec_status():
    """Get sample sets with SEC analysis status"""
    try:
        # Get FB samples and group them
        fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2)
        grouped = defaultdict(list)

        for sample in fb_samples:
            key = (sample.project, sample.sip_number, sample.development_stage)
            grouped[key].append(sample.sample_number)

        table_data = []
        for (project, sip, dev_stage), sample_nums in grouped.items():
            if not sample_nums:
                continue

            sorted_nums = sorted(sample_nums)
            sample_ids = [f"FB{n}" for n in sorted_nums]
            sample_range = f"FB{sorted_nums[0]} to FB{sorted_nums[-1]}"

            # Check SEC analysis status for this sample set
            sec_status, sec_actions = get_sec_status_for_sample_set(sample_ids)

            table_data.append({
                "project": project or "",
                "sip": sip or "",
                "development_stage": dev_stage or "",
                "range": sample_range,
                "count": len(sample_ids),
                "sec_status": sec_status,
                "sec_actions": sec_actions,
                "sample_ids": sample_ids  # Store for internal use
            })

        return table_data
    except Exception as e:
        print(f"Error getting sample sets: {e}")
        return []


def get_sec_status_for_sample_set(sample_ids):
    """Determine SEC analysis status for a sample set"""
    try:
        # Check if LimsSampleAnalysis records exist for these samples
        analysis_records = LimsSampleAnalysis.objects.filter(
            sample_id__in=sample_ids,
            sample_type=2
        )

        # Count records with SEC results
        with_sec_results = analysis_records.filter(sec_result__isnull=False).count()
        total_analysis_records = analysis_records.count()
        total_samples = len(sample_ids)

        # Create sample set parameter for URL
        sample_set_param = ",".join(sample_ids)

        if total_analysis_records == 0:
            # No analysis requested yet
            status = "⚪ Not Requested"
            actions = f"[📊 Request SEC Analysis](/sec/request?samples={sample_set_param})"

        elif with_sec_results == total_samples:
            # All samples have SEC results
            status = "✅ Complete"
            actions = f"[📈 View SEC Report](/sec/analyze?samples={sample_set_param})"

        elif total_analysis_records == total_samples:
            # All samples have analysis records but not all have SEC results
            if with_sec_results > 0:
                status = f"🔄 Partial ({with_sec_results}/{total_samples})"
                actions = f"[📈 View/Complete SEC](/sec/analyze?samples={sample_set_param})"
            else:
                status = "🔄 In Progress"
                actions = f"[📈 Create SEC Report](/sec/analyze?samples={sample_set_param})"
        else:
            # Partial analysis records
            status = f"🔄 Partial ({total_analysis_records}/{total_samples})"
            actions = f"[📊 Complete Request](/sec/request?samples={sample_set_param}) | [📈 Analyze Available](/sec/analyze?samples={sample_set_param})"

        return status, actions

    except Exception as e:
        print(f"Error checking SEC status: {e}")
        return "❌ Error", ""


def load_all_fb_samples_data():
    """Load all FB samples with SEC status and recovery calculations"""
    samples = LimsUpstreamSamples.objects.filter(sample_type=2).order_by("-sample_number")
    data = []

    for sample in samples:
        # Calculate recoveries
        fast_pro_a, a280 = calculate_recoveries(sample)

        # Check SEC status
        sample_id = f"FB{sample.sample_number}"
        sec_status = get_sample_sec_status(sample_id)

        # Build report link
        report_link = ""
        try:
            analysis = LimsSampleAnalysis.objects.filter(sample_id=sample_id).first()
            if analysis and hasattr(analysis, 'sec_result') and analysis.sec_result:
                report_link = f"[🔗 SEC Report](/sec/analyze?samples={sample_id})"
        except Exception:
            pass

        data.append({
            "sample_number": sample.sample_number,
            "project": sample.project or "",
            "cell_line": sample.cell_line or "",
            "harvest_date": sample.harvest_date.strftime("%Y-%m-%d") if sample.harvest_date else None,
            "development_stage": sample.development_stage or "",
            "sip_number": sample.sip_number or "",
            "analyst": sample.analyst or "",
            "hf_octet_titer": sample.hf_octet_titer,
            "pro_aqa_hf_titer": sample.pro_aqa_hf_titer,
            "sec_status": sec_status,
            "report_link": report_link
        })

    return data


def get_sample_sec_status(sample_id):
    """Get SEC analysis status for a single sample"""
    try:
        analysis = LimsSampleAnalysis.objects.filter(sample_id=sample_id, sample_type=2).first()

        if not analysis:
            return "⚪ Not Requested"

        if hasattr(analysis, 'sec_result') and analysis.sec_result:
            return "✅ Complete"
        else:
            return "🔄 In Progress"

    except Exception as e:
        print(f"Error checking SEC status for {sample_id}: {e}")
        return "❌ Error"


def calculate_recoveries(sample):
    """Calculate recovery percentages for a sample"""
    fast_pro_a_recovery = None
    a280_recovery = None

    try:
        if all([
            sample.proa_eluate_volume is not None,
            sample.pro_aqa_e_titer is not None,
            sample.hccf_loading_volume is not None,
            sample.pro_aqa_hf_titer is not None
        ]):
            fast_pro_a_recovery = (
                                          sample.proa_eluate_volume * sample.pro_aqa_e_titer
                                  ) / (
                                          sample.hccf_loading_volume * sample.pro_aqa_hf_titer
                                  ) * 100

        if all([
            sample.proa_eluate_volume is not None,
            sample.proa_eluate_a280_conc is not None,
            sample.hccf_loading_volume is not None,
            sample.pro_aqa_hf_titer is not None
        ]):
            a280_recovery = (
                                    sample.proa_eluate_volume * sample.proa_eluate_a280_conc
                            ) / (
                                    sample.hccf_loading_volume * sample.pro_aqa_hf_titer
                            ) * 100
    except ZeroDivisionError:
        pass

    return (
        round(fast_pro_a_recovery, 1) if fast_pro_a_recovery is not None else None,
        round(a280_recovery, 1) if a280_recovery is not None else None,
    )


def update_sample_data(table_data):
    """Update sample data in database"""
    updated = 0
    errors = 0

    editable_fields = [
        "cell_line", "harvest_date", "development_stage", "hf_octet_titer",
        "hccf_loading_volume", "sip_number", "analyst", "pro_aqa_hf_titer",
        "pro_aqa_e_titer", "proa_eluate_a280_conc", "proa_eluate_volume", "note"
    ]

    for row in table_data:
        try:
            update_data = {field: row.get(field) or None for field in editable_fields}
            LimsUpstreamSamples.objects.filter(
                sample_number=row["sample_number"],
                sample_type=2
            ).update(**update_data)
            updated += 1
        except Exception as e:
            print(f"Update failed for sample {row.get('sample_number')}: {e}")
            errors += 1

    return updated, errors


def save_sample_data(table_data, project, vessel_type, dev_stage, analyst, sip_number):
    """Save new sample data to database"""
    created = 0
    skipped = 0
    errors = 0

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

            # Also create LimsSampleAnalysis entry
            LimsSampleAnalysis.objects.update_or_create(
                sample_id=f'FB{row["sample_number"]}',
                sample_type=2,
                defaults={
                    "sample_date": row.get("harvest_date") or None,
                    "project_id": project,
                    "description": row.get("description", ""),
                    "notes": row.get("note", ""),
                    "analyst": analyst or "",
                    "dn": None,
                    "a280_result": None
                }
            )

            created += 1 if created_flag else 0

        except Exception as e:
            print(f"❌ Error saving sample {row.get('sample_number')}: {e}")
            errors += 1

    return created, skipped, errors