# config/app_urls.py
"""
Application URLs configuration for embedded apps and external integrations
"""

from typing import Dict, Optional
from urllib.parse import urlencode

# Base URLs for different app categories
BASE_URLS = {
    "dash_apps": "/plotly_integration/dash-app/app/",
    "protein_engineering": "/protein_engineering/dash-app/app/",
    "api": "/api/",
    "admin": "/admin/"
}

# External Dash application URLs
EXTERNAL_APPS = {
    # SEC Analysis Applications
    "sec_report_v2": {
        "url": "/plotly_integration/dash-app/app/SecReportApp2/",
        "name": "SEC Report App v2",
        "description": "Size Exclusion Chromatography analysis and reporting",
        "category": "analytics",
        "supports_embedding": True,
        "parameters": ["report_id", "samples", "mode", "hide_report_tab"]
    },

    "sec_report_v3": {
        "url": "/plotly_integration/dash-app/app/SecReportApp3/",
        "name": "SEC Report App v3",
        "description": "Enhanced SEC analysis application",
        "category": "analytics",
        "supports_embedding": True,
        "parameters": ["report_id", "samples", "mode"]
    },

    # Titer Analysis
    "titer_report": {
        "url": "/plotly_integration/dash-app/app/TiterReportApp/",
        "name": "Titer Report App",
        "description": "Protein titer analysis and reporting",
        "category": "analytics",
        "supports_embedding": True,
        "parameters": ["report_id", "samples"]
    },

    # Column Analysis
    "column_analysis": {
        "url": "/plotly_integration/dash-app/app/ColumnUsageApp/",
        "name": "Column Analysis App",
        "description": "Chromatography column usage tracking",
        "category": "equipment",
        "supports_embedding": True,
        "parameters": ["column_id", "date_range"]
    },

    # Sample Management
    "cld_sample_manager": {
        "url": "/plotly_integration/dash-app/app/CLDSampleManagementApp/",
        "name": "CLD Sample Manager",
        "description": "Cell Line Development sample management",
        "category": "samples",
        "supports_embedding": False,
        "parameters": []
    },

    "cld_sample_manager_v2": {
        "url": "/plotly_integration/dash-app/app/CLDSampleManagementApp2/",
        "name": "CLD Sample Manager v2",
        "description": "Enhanced CLD sample management",
        "category": "samples",
        "supports_embedding": False,
        "parameters": []
    },

    "upstream_sample_manager": {
        "url": "/plotly_integration/dash-app/app/UPSampleManagementApp/",
        "name": "Upstream Sample Manager",
        "description": "Upstream process sample management",
        "category": "samples",
        "supports_embedding": False,
        "parameters": []
    },

    # Database Management
    "database_manager": {
        "url": "/plotly_integration/dash-app/app/DatabaseManagerApp/",
        "name": "Database Manager",
        "description": "Database import and management tools",
        "category": "admin",
        "supports_embedding": False,
        "parameters": []
    },

    "report_creator": {
        "url": "/plotly_integration/dash-app/app/ReportApp/",
        "name": "Report Creator",
        "description": "General report creation and management",
        "category": "reports",
        "supports_embedding": False,
        "parameters": []
    },

    # LIMS Applications
    "dn_assignment": {
        "url": "/plotly_integration/dash-app/app/DnAssignmentApp/",
        "name": "DN Assignment",
        "description": "Downstream experiment assignment management",
        "category": "lims",
        "supports_embedding": False,
        "parameters": []
    },

    "sample_analysis": {
        "url": "/plotly_integration/dash-app/app/SampleAnalysisApp/",
        "name": "Sample Analysis",
        "description": "Sample analysis tracking and management",
        "category": "lims",
        "supports_embedding": True,
        "parameters": ["sample_id", "analysis_type"]
    },

    # Analytical Applications
    "ce_sds_import": {
        "url": "/plotly_integration/dash-app/app/CeSdsImportManagerApp/",
        "name": "CE-SDS Data Import",
        "description": "CE-SDS data import and processing",
        "category": "analytical",
        "supports_embedding": False,
        "parameters": []
    },

    "ce_sds_report": {
        "url": "/plotly_integration/dash-app/app/CreateCESDSReportApp/",
        "name": "CE-SDS Report",
        "description": "CE-SDS analysis reporting",
        "category": "analytical",
        "supports_embedding": True,
        "parameters": ["report_id", "samples"]
    },

    "ce_sds_analysis": {
        "url": "/plotly_integration/dash-app/app/CESDSReportViewerApp/",
        "name": "CE-SDS Analysis",
        "description": "CE-SDS analysis and visualization",
        "category": "analytical",
        "supports_embedding": True,
        "parameters": ["report_id"]
    },

    # cIEF Applications
    "cief_import": {
        "url": "/plotly_integration/dash-app/app/cIEFImportManagerApp/",
        "name": "cIEF Data Import",
        "description": "cIEF data import and processing",
        "category": "analytical",
        "supports_embedding": False,
        "parameters": []
    },

    "cief_report": {
        "url": "/plotly_integration/dash-app/app/cIEFReportApp/",
        "name": "cIEF Report",
        "description": "cIEF analysis reporting",
        "category": "analytical",
        "supports_embedding": True,
        "parameters": ["report_id", "samples"]
    },

    "cief_analysis": {
        "url": "/plotly_integration/dash-app/app/cIEFReportViewerApp/",
        "name": "cIEF Analysis",
        "description": "cIEF analysis and visualization",
        "category": "analytical",
        "supports_embedding": True,
        "parameters": ["report_id"]
    }
}

# Internal dashboard routes
INTERNAL_ROUTES = {
    "dashboard_home": "/",
    "fb_samples_view": "/fb-samples/view",
    "fb_samples_sets": "/fb-samples/sets",
    "fb_samples_create": "/fb-samples/create",
    "sec_dashboard": "/sec/dashboard",
    "sec_sample_sets": "/sec/sample-sets",
    "sec_reports": "/sec/reports",
    "sec_request": "/sec/request",
    "sec_analyze": "/sec/analyze",
    "settings": "/settings"
}


def get_app_url(app_name: str) -> Optional[str]:
    """
    Get URL for an external application

    Args:
        app_name (str): Name of the application

    Returns:
        str: Application URL or None if not found
    """
    app_config = EXTERNAL_APPS.get(app_name)
    return app_config["url"] if app_config else None


def build_app_url(app_name: str, **params) -> Optional[str]:
    """
    Build URL for an external application with parameters

    Args:
        app_name (str): Name of the application
        **params: URL parameters to include

    Returns:
        str: Complete application URL with parameters
    """
    base_url = get_app_url(app_name)
    if not base_url:
        return None

    app_config = EXTERNAL_APPS.get(app_name, {})
    supported_params = app_config.get("parameters", [])

    # Filter parameters to only include supported ones
    filtered_params = {k: v for k, v in params.items() if k in supported_params}

    if filtered_params:
        query_string = urlencode(filtered_params, doseq=True)
        return f"{base_url}?{query_string}"

    return base_url


def get_apps_by_category(category: str) -> Dict[str, dict]:
    """
    Get all applications in a specific category

    Args:
        category (str): Application category

    Returns:
        dict: Applications in the category
    """
    return {
        name: config for name, config in EXTERNAL_APPS.items()
        if config.get("category") == category
    }


def get_embeddable_apps() -> Dict[str, dict]:
    """
    Get all applications that support embedding

    Returns:
        dict: Embeddable applications
    """
    return {
        name: config for name, config in EXTERNAL_APPS.items()
        if config.get("supports_embedding", False)
    }


def build_sec_analysis_url(sample_ids=None, report_id=None, mode="samples", hide_report_tab=True):
    """
    Build URL for SEC analysis with specific parameters

    Args:
        sample_ids (list): List of sample IDs to analyze
        report_id (int): Specific report to view
        mode (str): Analysis mode ('samples' or 'report')
        hide_report_tab (bool): Hide the report selection tab

    Returns:
        str: Complete SEC analysis URL
    """
    params = {}

    if report_id:
        params["report_id"] = report_id

    if sample_ids:
        params["samples"] = ",".join(sample_ids)

    if mode:
        params["mode"] = mode

    if hide_report_tab:
        params["hide_report_tab"] = "true"

    return build_app_url("sec_report_v2", **params)


def build_sample_analysis_url(sample_id, analysis_type=None):
    """
    Build URL for sample analysis application

    Args:
        sample_id (str): Sample ID to analyze
        analysis_type (str): Type of analysis

    Returns:
        str: Sample analysis URL
    """
    params = {"sample_id": sample_id}

    if analysis_type:
        params["analysis_type"] = analysis_type

    return build_app_url("sample_analysis", **params)


def get_navigation_links():
    """
    Get navigation links for the dashboard

    Returns:
        dict: Navigation structure
    """
    return {
        "main": [
            {"name": "Dashboard", "url": INTERNAL_ROUTES["dashboard_home"], "icon": "fa-tachometer-alt"},
        ],
        "samples": [
            {"name": "View All Samples", "url": INTERNAL_ROUTES["fb_samples_view"], "icon": "fa-vial"},
            {"name": "Sample Sets", "url": INTERNAL_ROUTES["fb_samples_sets"], "icon": "fa-layer-group"},
            {"name": "Add Samples", "url": INTERNAL_ROUTES["fb_samples_create"], "icon": "fa-plus"},
        ],
        "sec_analytics": [
            {"name": "SEC Overview", "url": INTERNAL_ROUTES["sec_dashboard"], "icon": "fa-chart-bar"},
            {"name": "SEC Sample Sets", "url": INTERNAL_ROUTES["sec_sample_sets"], "icon": "fa-microscope"},
            {"name": "SEC Reports", "url": INTERNAL_ROUTES["sec_reports"], "icon": "fa-chart-line"},
        ],
        "external_apps": [
            {"name": "Database Manager", "url": get_app_url("database_manager"), "icon": "fa-database"},
            {"name": "Report Creator", "url": get_app_url("report_creator"), "icon": "fa-file-alt"},
            {"name": "DN Assignment", "url": get_app_url("dn_assignment"), "icon": "fa-tasks"},
        ],
        "system": [
            {"name": "Settings", "url": INTERNAL_ROUTES["settings"], "icon": "fa-cogs"},
        ]
    }


def validate_app_parameters(app_name: str, **params) -> Dict[str, str]:
    """
    Validate parameters for an application

    Args:
        app_name (str): Application name
        **params: Parameters to validate

    Returns:
        dict: Valid parameters only
    """
    app_config = EXTERNAL_APPS.get(app_name, {})
    supported_params = app_config.get("parameters", [])

    return {k: v for k, v in params.items() if k in supported_params}


# API endpoints for data integration
API_ENDPOINTS = {
    "sec_results": "/api/sec-results/",
    "sample_analysis": "/api/sample-analysis/",
    "reports": "/api/reports/",
    "samples": "/api/samples/",
    "sample_sets": "/api/sample-sets/",
    "analysis_status": "/api/analysis-status/"
}


def get_api_url(endpoint_name: str, resource_id: Optional[str] = None) -> str:
    """
    Get API endpoint URL

    Args:
        endpoint_name (str): Name of the API endpoint
        resource_id (str): Optional resource ID

    Returns:
        str: Complete API URL
    """
    base_url = API_ENDPOINTS.get(endpoint_name, "")

    if resource_id:
        return f"{base_url}{resource_id}/"

    return base_url