# samples/callbacks/analysis_requests.py
"""
Callbacks for handling SEC analysis requests
"""

from datetime import datetime
from dash import Input, Output, State, callback, ctx, no_update
import dash
from plotly_integration.models import (
    LimsUpstreamSamples, LimsSampleAnalysis, LimsSecResult
)
from ...config.analysis_types import AnalysisType, AnalysisStatus


def create_analysis_request_callbacks(app):
    """Create callbacks for SEC analysis requests"""

    @app.callback(
        Output("sec-request-status", "children"),
        Output("sec-request-status", "style"),
        Input("request-sec-analysis-btn", "n_clicks"),
        State("selected-sample-ids", "data"),
        prevent_initial_call=True
    )
    def handle_sec_analysis_request(n_clicks, sample_ids):
        """Handle SEC analysis request for selected samples"""
        if not sample_ids:
            return "❌ No samples selected", {"color": "red"}

        try:
            result = request_sec_analysis_for_samples(sample_ids)
            return result["message"], {"color": result["color"]}
        except Exception as e:
            return f"❌ Error requesting analysis: {str(e)}", {"color": "red"}

    @app.callback(
        Output("bulk-sec-request-status", "children"),
        Input("bulk-request-sec-btn", "n_clicks"),
        State("sample-sets-table", "data"),
        prevent_initial_call=True
    )
    def handle_bulk_sec_request(n_clicks, sample_sets_data):
        """Handle bulk SEC analysis request for all pending sample sets"""
        if not sample_sets_data:
            return "❌ No sample sets available"

        try:
            # Find sample sets that need SEC analysis
            pending_sets = [
                row for row in sample_sets_data
                if "Not Requested" in row.get("sec_status", "") or "Partial" in row.get("sec_status", "")
            ]

            if not pending_sets:
                return "✅ No pending SEC requests needed"

            total_requested = 0
            total_errors = 0

            for sample_set in pending_sets:
                sample_ids = sample_set.get("sample_ids", [])
                result = request_sec_analysis_for_samples(sample_ids)

                if result["success"]:
                    total_requested += result["requested"]
                else:
                    total_errors += 1

            if total_errors == 0:
                return f"✅ Requested SEC analysis for {total_requested} samples across {len(pending_sets)} sample sets"
            else:
                return f"⚠️ Requested SEC for {total_requested} samples, {total_errors} sets had errors"

        except Exception as e:
            return f"❌ Error processing bulk request: {str(e)}"


def request_sec_analysis_for_samples(sample_ids):
    """
    Request SEC analysis for a list of sample IDs

    Args:
        sample_ids (list): List of sample IDs (e.g., ['FB123', 'FB124'])

    Returns:
        dict: Result with success status, message, and counts
    """
    try:
        requested = 0
        already_exists = 0
        errors = 0

        for sample_id in sample_ids:
            try:
                # Extract sample number from ID (e.g., FB123 -> 123)
                sample_number = int(sample_id.replace('FB', ''))

                # Check if the FB sample exists
                fb_sample = LimsUpstreamSamples.objects.filter(
                    sample_number=sample_number,
                    sample_type=2
                ).first()

                if not fb_sample:
                    print(f"Warning: FB sample {sample_id} not found")
                    errors += 1
                    continue

                # Create or update LimsSampleAnalysis record
                analysis, created = LimsSampleAnalysis.objects.update_or_create(
                    sample_id=sample_id,
                    sample_type=2,
                    defaults={
                        "sample_date": fb_sample.harvest_date,
                        "project_id": fb_sample.project or "Unknown",
                        "description": f"SEC analysis requested for {sample_id}",
                        "analyst": fb_sample.analyst or "System",
                        "notes": f"SEC analysis requested on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        "status": "in_progress"
                    }
                )

                if created:
                    requested += 1
                else:
                    # Check if it already has SEC results
                    if hasattr(analysis, 'sec_result') and analysis.sec_result:
                        already_exists += 1
                    else:
                        # Update the existing record to ensure it's marked for SEC
                        analysis.notes = f"SEC analysis re-requested on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        analysis.save()
                        requested += 1

            except ValueError as e:
                print(f"Error parsing sample ID {sample_id}: {e}")
                errors += 1
            except Exception as e:
                print(f"Error processing sample {sample_id}: {e}")
                errors += 1

        # Build result message
        total_samples = len(sample_ids)
        success = errors < total_samples

        if success:
            if requested > 0 and already_exists > 0:
                message = f"✅ Requested SEC analysis for {requested} samples, {already_exists} already had analysis records"
                color = "green"
            elif requested > 0:
                message = f"✅ Successfully requested SEC analysis for {requested} samples"
                color = "green"
            elif already_exists > 0:
                message = f"ℹ️ All {already_exists} samples already have analysis records"
                color = "blue"
            else:
                message = "⚠️ No new analysis requests created"
                color = "orange"
        else:
            message = f"❌ Processed {requested} samples successfully, {errors} had errors"
            color = "red"

        return {
            "success": success,
            "message": message,
            "color": color,
            "requested": requested,
            "already_exists": already_exists,
            "errors": errors
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error requesting SEC analysis: {str(e)}",
            "color": "red",
            "requested": 0,
            "already_exists": 0,
            "errors": len(sample_ids)
        }


def check_sec_analysis_status(sample_ids):
    """
    Check SEC analysis status for a list of sample IDs

    Args:
        sample_ids (list): List of sample IDs

    Returns:
        dict: Status summary
    """
    try:
        status_counts = {
            "not_requested": 0,
            "in_progress": 0,
            "complete": 0,
            "error": 0
        }

        sample_details = []

        for sample_id in sample_ids:
            try:
                analysis = LimsSampleAnalysis.objects.filter(
                    sample_id=sample_id,
                    sample_type=2
                ).first()

                if not analysis:
                    status = "not_requested"
                elif hasattr(analysis, 'sec_result') and analysis.sec_result:
                    status = "complete"
                else:
                    status = "in_progress"

                status_counts[status] += 1
                sample_details.append({
                    "sample_id": sample_id,
                    "status": status,
                    "analysis_record": analysis is not None
                })

            except Exception as e:
                print(f"Error checking status for {sample_id}: {e}")
                status_counts["error"] += 1
                sample_details.append({
                    "sample_id": sample_id,
                    "status": "error",
                    "analysis_record": False
                })

        return {
            "status_counts": status_counts,
            "sample_details": sample_details,
            "total_samples": len(sample_ids)
        }

    except Exception as e:
        print(f"Error checking SEC analysis status: {e}")
        return {
            "status_counts": {"error": len(sample_ids)},
            "sample_details": [],
            "total_samples": len(sample_ids)
        }


def get_pending_sec_requests():
    """
    Get all samples that have analysis records but no SEC results

    Returns:
        list: Sample IDs with pending SEC analysis
    """
    try:
        # Find analysis records without SEC results
        pending_analyses = LimsSampleAnalysis.objects.filter(
            sample_type=2,
            sec_result__isnull=True
        ).values_list('sample_id', flat=True)

        return list(pending_analyses)

    except Exception as e:
        print(f"Error getting pending SEC requests: {e}")
        return []


def cancel_sec_analysis_request(sample_ids):
    """
    Cancel SEC analysis request by removing LimsSampleAnalysis records

    Args:
        sample_ids (list): List of sample IDs to cancel

    Returns:
        dict: Result with success status and message
    """
    try:
        cancelled = 0
        not_found = 0
        had_results = 0

        for sample_id in sample_ids:
            try:
                analysis = LimsSampleAnalysis.objects.filter(
                    sample_id=sample_id,
                    sample_type=2
                ).first()

                if not analysis:
                    not_found += 1
                    continue

                # Don't cancel if it already has SEC results
                if hasattr(analysis, 'sec_result') and analysis.sec_result:
                    had_results += 1
                    continue

                # Remove the analysis record
                analysis.delete()
                cancelled += 1

            except Exception as e:
                print(f"Error cancelling request for {sample_id}: {e}")

        if cancelled > 0:
            message = f"✅ Cancelled SEC analysis requests for {cancelled} samples"
            if had_results > 0:
                message += f" ({had_results} samples with existing results were not cancelled)"
            success = True
        else:
            message = "⚠️ No SEC analysis requests were cancelled"
            success = False

        return {
            "success": success,
            "message": message,
            "cancelled": cancelled,
            "not_found": not_found,
            "had_results": had_results
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error cancelling SEC analysis requests: {str(e)}",
            "cancelled": 0,
            "not_found": 0,
            "had_results": 0
        }


def get_sample_set_analysis_summary(sample_ids):
    """
    Get analysis summary for a sample set

    Args:
        sample_ids (list): List of sample IDs in the set

    Returns:
        dict: Summary information about the sample set's analysis status
    """
    try:
        # Get FB sample information
        sample_numbers = [int(sid.replace('FB', '')) for sid in sample_ids if sid.startswith('FB')]
        fb_samples = LimsUpstreamSamples.objects.filter(
            sample_number__in=sample_numbers,
            sample_type=2
        )

        # Get analysis status
        analysis_status = check_sec_analysis_status(sample_ids)

        # Build summary
        summary = {
            "sample_count": len(sample_ids),
            "fb_samples_found": fb_samples.count(),
            "project": fb_samples.first().project if fb_samples.exists() else "Unknown",
            "sip_number": fb_samples.first().sip_number if fb_samples.exists() else "Unknown",
            "development_stage": fb_samples.first().development_stage if fb_samples.exists() else "Unknown",
            "analysis_status": analysis_status["status_counts"],
            "can_request_sec": analysis_status["status_counts"]["not_requested"] > 0,
            "can_view_sec": analysis_status["status_counts"]["complete"] > 0,
            "has_pending": analysis_status["status_counts"]["in_progress"] > 0
        }

        return summary

    except Exception as e:
        print(f"Error getting sample set summary: {e}")
        return {
            "sample_count": len(sample_ids),
            "fb_samples_found": 0,
            "project": "Error",
            "sip_number": "Error",
            "development_stage": "Error",
            "analysis_status": {"error": len(sample_ids)},
            "can_request_sec": False,
            "can_view_sec": False,
            "has_pending": False
        }