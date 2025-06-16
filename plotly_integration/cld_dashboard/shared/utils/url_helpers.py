# shared/utils/url_helpers.py
"""
URL generation helpers for the CLD Dashboard
"""

from urllib.parse import urlencode
import json


def build_url(base_path, **params):
    """
    Build a URL with query parameters

    Args:
        base_path (str): Base URL path
        **params: Query parameters to add

    Returns:
        str: Complete URL with parameters
    """
    if params:
        query_string = urlencode(params, doseq=True)
        return f"{base_path}?{query_string}"
    return base_path


def build_sec_report_url(sample_ids=None, report_id=None, hide_report_tab=True, mode=None):
    """
    Build URL for SEC Report App with appropriate parameters

    Args:
        sample_ids (list): List of sample IDs to analyze
        report_id (int): Specific report to view
        hide_report_tab (bool): Hide the report selection tab
        mode (str): View mode ('samples' or 'report')

    Returns:
        str: Complete SEC report URL
    """
    base_url = "/plotly_integration/dash-app/app/SecReportApp2/"
    params = {}

    if report_id:
        params['report_id'] = report_id

    if sample_ids:
        params['samples'] = ','.join(sample_ids)
        if not mode:
            mode = 'samples'

    if mode:
        params['mode'] = mode

    if hide_report_tab:
        params['hide_report_tab'] = 'true'

    return build_url(base_url, **params)


def build_dashboard_url(page=None, **params):
    """
    Build URL for dashboard pages

    Args:
        page (str): Dashboard page ('samples', 'sec', 'reports', etc.)
        **params: Additional parameters

    Returns:
        str: Dashboard URL
    """
    if page:
        base_url = f"/{page}"
    else:
        base_url = "/"

    return build_url(base_url, **params)


def build_sample_set_action_url(action, sample_ids):
    """
    Build URL for sample set actions

    Args:
        action (str): Action type ('request_sec', 'view_sec', etc.)
        sample_ids (list): List of sample IDs

    Returns:
        str: Action URL
    """
    sample_param = ','.join(sample_ids)

    if action == 'request_sec':
        return f"/sec/request?samples={sample_param}"
    elif action == 'view_sec':
        return build_sec_report_url(sample_ids=sample_ids)
    elif action == 'create_sec':
        return build_sec_report_url(sample_ids=sample_ids, hide_report_tab=True)
    else:
        return f"/action/{action}?samples={sample_param}"


def encode_sample_set_data(sample_set_dict):
    """
    Encode sample set data for URL transmission

    Args:
        sample_set_dict (dict): Sample set data

    Returns:
        str: Encoded data for URL
    """
    return json.dumps(sample_set_dict).replace('"', '%22').replace(' ', '%20')


def decode_sample_set_data(encoded_data):
    """
    Decode sample set data from URL

    Args:
        encoded_data (str): Encoded data from URL

    Returns:
        dict: Decoded sample set data
    """
    try:
        decoded = encoded_data.replace('%22', '"').replace('%20', ' ')
        return json.loads(decoded)
    except (json.JSONDecodeError, AttributeError):
        return {}


def get_external_app_urls():
    """
    Get URLs for external applications

    Returns:
        dict: Mapping of app names to URLs
    """
    return {
        'sec_report': '/plotly_integration/dash-app/app/SecReportApp2/',
        'sec_report_v3': '/plotly_integration/dash-app/app/SecReportApp3/',
        'titer_report': '/plotly_integration/dash-app/app/TiterReportApp/',
        'column_analysis': '/plotly_integration/dash-app/app/ColumnUsageApp/',
        'database_manager': '/plotly_integration/dash-app/app/DatabaseManagerApp/',
        'create_report': '/plotly_integration/dash-app/app/ReportApp/',
        'cld_sample_manager': '/plotly_integration/dash-app/app/CLDSampleManagementApp/',
        'upstream_sample_manager': '/plotly_integration/dash-app/app/UPSampleManagementApp/'
    }


def build_external_app_url(app_name, **params):
    """
    Build URL for external applications

    Args:
        app_name (str): Name of the external app
        **params: Query parameters

    Returns:
        str: Complete external app URL
    """
    urls = get_external_app_urls()
    base_url = urls.get(app_name)

    if not base_url:
        raise ValueError(f"Unknown app name: {app_name}")

    return build_url(base_url, **params)


def parse_sample_ids_from_url(sample_param):
    """
    Parse sample IDs from URL parameter

    Args:
        sample_param (str): Comma-separated sample IDs

    Returns:
        list: List of sample IDs
    """
    if not sample_param:
        return []

    return [s.strip() for s in sample_param.split(',') if s.strip()]


def build_markdown_link(text, url, target="_blank"):
    """
    Build markdown link for DataTable

    Args:
        text (str): Link text
        url (str): Link URL
        target (str): Link target

    Returns:
        str: Markdown formatted link
    """
    if target:
        return f"[{text}]({url})"
    else:
        return f"[{text}]({url})"


def build_action_buttons_markdown(sample_ids, current_status="not_requested"):
    """
    Build action buttons in markdown format based on SEC status

    Args:
        sample_ids (list): List of sample IDs
        current_status (str): Current SEC analysis status

    Returns:
        str: Markdown formatted action buttons
    """
    sample_param = ','.join(sample_ids)

    if current_status == "not_requested":
        return f"[📊 Request SEC Analysis](/sec/request?samples={sample_param})"

    elif current_status == "complete":
        return f"[📈 View SEC Report]({build_sec_report_url(sample_ids=sample_ids)})"

    elif current_status in ["in_progress", "partial"]:
        request_url = f"/sec/request?samples={sample_param}"
        view_url = build_sec_report_url(sample_ids=sample_ids)
        return f"[📊 Complete Request]({request_url}) | [📈 View Analysis]({view_url})"

    else:
        return f"[📈 Analyze]({build_sec_report_url(sample_ids=sample_ids)})"


def get_breadcrumb_links(current_page):
    """
    Generate breadcrumb navigation links

    Args:
        current_page (str): Current page identifier

    Returns:
        list: List of breadcrumb items
    """
    breadcrumbs = [
        {"text": "Dashboard", "url": "/", "active": False}
    ]

    if current_page.startswith("fb-samples"):
        breadcrumbs.append({"text": "FB Samples", "url": "/fb-samples/view", "active": False})

        if "sets" in current_page:
            breadcrumbs.append({"text": "Sample Sets", "url": "/fb-samples/sets", "active": True})
        elif "create" in current_page:
            breadcrumbs.append({"text": "Create Samples", "url": "/fb-samples/create", "active": True})
        else:
            breadcrumbs[-1]["active"] = True

    elif current_page.startswith("sec"):
        breadcrumbs.append({"text": "SEC Analytics", "url": "/sec/dashboard", "active": False})

        if "sample-sets" in current_page:
            breadcrumbs.append({"text": "SEC Sample Sets", "url": "/sec/sample-sets", "active": True})
        elif "reports" in current_page:
            breadcrumbs.append({"text": "SEC Reports", "url": "/sec/reports", "active": True})
        else:
            breadcrumbs[-1]["active"] = True

    return breadcrumbs