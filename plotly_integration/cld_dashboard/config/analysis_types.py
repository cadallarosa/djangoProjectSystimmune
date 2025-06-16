# config/analysis_types.py
"""
Analysis type constants and configuration for CLD Dashboard
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class AnalysisType(Enum):
    """Analysis type enumeration"""
    SEC = 1
    TITER = 2
    MASS_CHECK = 3
    GLYCAN = 4
    CE_SDS = 5
    CIEF = 6
    HCP = 7
    PROA = 8


class AnalysisStatus(Enum):
    """Analysis status enumeration"""
    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETE = "complete"
    ERROR = "error"
    REVIEW = "review"


@dataclass
class AnalysisConfig:
    """Configuration for an analysis type"""
    id: int
    name: str
    display_name: str
    description: str
    icon: str
    color: str
    app_url: str
    model_name: str
    result_fields: List[str]
    required_fields: List[str]
    optional_fields: List[str]


# Analysis type configurations
ANALYSIS_CONFIGS: Dict[AnalysisType, AnalysisConfig] = {
    AnalysisType.SEC: AnalysisConfig(
        id=1,
        name="sec",
        display_name="SEC Analysis",
        description="Size Exclusion Chromatography analysis for protein aggregation",
        icon="fa-microscope",
        color="primary",
        app_url="/plotly_integration/dash-app/app/SecReportApp2/",
        model_name="LimsSecResult",
        result_fields=["main_peak", "hmw", "lmw"],
        required_fields=["sample_id"],
        optional_fields=["peak_data", "qc_pass", "report"]
    ),

    AnalysisType.TITER: AnalysisConfig(
        id=2,
        name="titer",
        display_name="Titer Analysis",
        description="Protein titer determination",
        icon="fa-flask",
        color="success",
        app_url="/plotly_integration/dash-app/app/TiterReportApp/",
        model_name="LimsTiterResult",
        result_fields=["titer"],
        required_fields=["sample_id"],
        optional_fields=["qc_pass"]
    ),

    AnalysisType.MASS_CHECK: AnalysisConfig(
        id=3,
        name="mass_check",
        display_name="Mass Check",
        description="Protein mass verification by LC-MS",
        icon="fa-balance-scale",
        color="info",
        app_url="/plotly_integration/dash-app/app/MassCheckApp/",
        model_name="LimsMassCheckResult",
        result_fields=["expected_mass", "observed_mass"],
        required_fields=["sample_id", "expected_mass", "observed_mass"],
        optional_fields=["notes"]
    ),

    AnalysisType.GLYCAN: AnalysisConfig(
        id=4,
        name="glycan",
        display_name="Glycan Analysis",
        description="Released N-glycan profiling by LC-MS",
        icon="fa-sugar",
        color="warning",
        app_url="/plotly_integration/dash-app/app/GlycanApp/",
        model_name="LimsReleasedGlycanResult",
        result_fields=["glycan_profile", "major_species"],
        required_fields=["sample_id", "glycan_profile"],
        optional_fields=["major_species", "notes"]
    ),

    AnalysisType.CE_SDS: AnalysisConfig(
        id=5,
        name="ce_sds",
        display_name="CE-SDS",
        description="Capillary Electrophoresis SDS analysis",
        icon="fa-wave-square",
        color="secondary",
        app_url="/plotly_integration/dash-app/app/CESDSApp/",
        model_name="LimsCeSdsResult",
        result_fields=["purity"],
        required_fields=["sample_id", "purity"],
        optional_fields=["band_pattern", "notes"]
    ),

    AnalysisType.CIEF: AnalysisConfig(
        id=6,
        name="cief",
        display_name="cIEF",
        description="Capillary Isoelectric Focusing",
        icon="fa-chart-area",
        color="dark",
        app_url="/plotly_integration/dash-app/app/cIEFApp/",
        model_name="LimsCiefResult",
        result_fields=["main_peak", "acidic_variants", "basic_variants"],
        required_fields=["sample_id", "main_peak", "acidic_variants", "basic_variants"],
        optional_fields=["notes"]
    ),

    AnalysisType.HCP: AnalysisConfig(
        id=7,
        name="hcp",
        display_name="HCP",
        description="Host Cell Protein quantification",
        icon="fa-virus",
        color="danger",
        app_url="/plotly_integration/dash-app/app/HCPApp/",
        model_name="LimsHcpResult",
        result_fields=["hcp_level"],
        required_fields=["sample_id", "hcp_level"],
        optional_fields=["unit", "notes"]
    ),

    AnalysisType.PROA: AnalysisConfig(
        id=8,
        name="proa",
        display_name="Protein A",
        description="Protein A leachate quantification",
        icon="fa-dna",
        color="info",
        app_url="/plotly_integration/dash-app/app/ProAApp/",
        model_name="LimsProaResult",
        result_fields=["proa_level"],
        required_fields=["sample_id", "proa_level"],
        optional_fields=["unit", "notes"]
    )
}


def get_analysis_config(analysis_type: AnalysisType) -> AnalysisConfig:
    """Get configuration for an analysis type"""
    return ANALYSIS_CONFIGS.get(analysis_type)


def get_analysis_config_by_id(analysis_id: int) -> Optional[AnalysisConfig]:
    """Get configuration by analysis ID"""
    for analysis_type, config in ANALYSIS_CONFIGS.items():
        if config.id == analysis_id:
            return config
    return None


def get_analysis_config_by_name(name: str) -> Optional[AnalysisConfig]:
    """Get configuration by analysis name"""
    for analysis_type, config in ANALYSIS_CONFIGS.items():
        if config.name == name:
            return config
    return None


# Status display configurations
STATUS_DISPLAY = {
    AnalysisStatus.NOT_REQUESTED: {
        "icon": "⚪",
        "text": "Not Requested",
        "color": "secondary",
        "description": "Analysis has not been requested for this sample"
    },
    AnalysisStatus.REQUESTED: {
        "icon": "📋",
        "text": "Requested",
        "color": "info",
        "description": "Analysis has been requested but not started"
    },
    AnalysisStatus.IN_PROGRESS: {
        "icon": "🔄",
        "text": "In Progress",
        "color": "warning",
        "description": "Analysis is currently being performed"
    },
    AnalysisStatus.PARTIAL: {
        "icon": "🔄",
        "text": "Partial",
        "color": "warning",
        "description": "Analysis is partially complete"
    },
    AnalysisStatus.COMPLETE: {
        "icon": "✅",
        "text": "Complete",
        "color": "success",
        "description": "Analysis has been completed successfully"
    },
    AnalysisStatus.ERROR: {
        "icon": "❌",
        "text": "Error",
        "color": "danger",
        "description": "An error occurred during analysis"
    },
    AnalysisStatus.REVIEW: {
        "icon": "👁️",
        "text": "Under Review",
        "color": "info",
        "description": "Analysis results are being reviewed"
    }
}


def get_status_display(status: AnalysisStatus) -> Dict[str, str]:
    """Get display configuration for an analysis status"""
    return STATUS_DISPLAY.get(status, STATUS_DISPLAY[AnalysisStatus.ERROR])


def format_status_display(status: AnalysisStatus, include_icon: bool = True) -> str:
    """Format status for display"""
    display = get_status_display(status)
    if include_icon:
        return f"{display['icon']} {display['text']}"
    return display['text']


# Sample type configurations
SAMPLE_TYPES = {
    1: {
        "name": "UP",
        "display_name": "Upstream",
        "description": "Upstream process samples",
        "prefix": "UP"
    },
    2: {
        "name": "FB",
        "display_name": "Fed Batch",
        "description": "Fed batch cell culture samples",
        "prefix": "FB"
    },
    3: {
        "name": "PD",
        "display_name": "Process Development",
        "description": "Process development samples",
        "prefix": "PD"
    }
}


def get_sample_type_config(sample_type_id: int) -> Optional[Dict]:
    """Get sample type configuration"""
    return SAMPLE_TYPES.get(sample_type_id)


def format_sample_id(sample_number: int, sample_type_id: int) -> str:
    """Format sample ID with appropriate prefix"""
    config = get_sample_type_config(sample_type_id)
    if config:
        return f"{config['prefix']}{sample_number}"
    return str(sample_number)


# Analysis priority configurations
ANALYSIS_PRIORITIES = {
    "high": {
        "name": "High",
        "color": "danger",
        "icon": "fa-exclamation",
        "description": "High priority analysis"
    },
    "medium": {
        "name": "Medium",
        "color": "warning",
        "icon": "fa-minus",
        "description": "Medium priority analysis"
    },
    "low": {
        "name": "Low",
        "color": "secondary",
        "icon": "fa-minus",
        "description": "Low priority analysis"
    }
}

# Validation rules for analysis results
VALIDATION_RULES = {
    AnalysisType.SEC: {
        "main_peak": {"min": 0, "max": 100, "unit": "%"},
        "hmw": {"min": 0, "max": 100, "unit": "%"},
        "lmw": {"min": 0, "max": 100, "unit": "%"}
    },
    AnalysisType.TITER: {
        "titer": {"min": 0, "max": 10000, "unit": "mg/L"}
    },
    AnalysisType.HCP: {
        "hcp_level": {"min": 0, "max": 10000, "unit": "ng/mg"}
    },
    AnalysisType.PROA: {
        "proa_level": {"min": 0, "max": 10000, "unit": "ng/mg"}
    }
}


def validate_analysis_result(analysis_type: AnalysisType, field: str, value: float) -> bool:
    """Validate analysis result value"""
    rules = VALIDATION_RULES.get(analysis_type, {})
    field_rules = rules.get(field, {})

    if not field_rules:
        return True  # No validation rules defined

    min_val = field_rules.get("min")
    max_val = field_rules.get("max")

    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False

    return True