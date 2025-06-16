# import re
# from plotly_integration.models import AktaResult
#
# def assign_dn_from_result_path(result_path):
#     """
#     Parses result_path to extract DN number from the last path segment
#     and assigns it to report_name in the format 'DN###'.
#     """
#     if not result_path:
#         return "❌ No result_path provided"
#
#     # Get the last component after the last slash
#     last_segment = result_path.strip().split("/")[-1]
#
#     # Search for DN followed by optional space and 3+ digits
#     match = re.search(r"DN\s*(\d{3,})", last_segment, re.IGNORECASE)
#     if not match:
#         return f"❌ No DN number found in: '{last_segment}'"
#
#     dn_number = match.group(1)
#     new_report_name = f"DN{dn_number}"
#
#     # Look up result by result_path
#     result = AktaResult.objects.filter(result_path=result_path).first()
#     if not result:
#         return f"❌ No AktaResult with result_path: {result_path}"
#
#     # Update if needed
#     if result.report_name != new_report_name:
#         result.report_name = new_report_name
#         result.save()
#         return f"✅ Updated report_name to {new_report_name} (result_id={result.result_id})"
#     else:
#         return f"⏩ Already set to {new_report_name} (result_id={result.result_id})"
#
# # Apply to all AktaResult entries
# for r in AktaResult.objects.exclude(result_path=None):
#     print(assign_dn_from_result_path(r.result_path))


import re
from plotly_integration.models import AktaResult

def assign_report_name_from_result_path(result_path):
    """
    Parses result_path to extract DN/FB/UP number from the last path segment,
    and assigns it to report_name (e.g., 'DN577', 'FB123', 'UP456').
    """
    if not result_path:
        return "❌ No result_path provided"

    # Get the last component after the last slash
    last_segment = result_path.strip().split("/")[-1]

    # Try DN / FB / UP match
    match = re.search(r"\b(DN|FB|UP)\s*(\d{3,})", last_segment, re.IGNORECASE)
    if not match:
        return f"❌ No DN/FB/UP number found in: '{last_segment}'"

    prefix = match.group(1).upper()  # 'DN', 'FB', or 'UP'
    number = match.group(2)
    new_report_name = f"{prefix}{number}"

    # Look up result
    result = AktaResult.objects.filter(result_path=result_path).first()
    if not result:
        return f"❌ No AktaResult with result_path: {result_path}"

    # Update if needed
    if result.report_name != new_report_name:
        result.report_name = new_report_name
        result.save()
        return f"✅ Updated report_name to {new_report_name} (result_id={result.result_id})"
    else:
        return f"⏩ Already set to {new_report_name} (result_id={result.result_id})"

# Apply to all AktaResult entries
for r in AktaResult.objects.exclude(result_path=None):
    print(assign_report_name_from_result_path(r.result_path))
