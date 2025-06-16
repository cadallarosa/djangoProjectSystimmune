# shared/styles/common_styles.py
"""
Common styles and constants for the CLD Dashboard
"""

# ================== TABLE STYLES ==================
TABLE_STYLE_CELL = {
    'textAlign': 'left',
    'fontSize': '11px',
    'fontFamily': 'Arial, sans-serif',
    'padding': '8px',
    'border': '1px solid #ddd',
    'minWidth': '100px',
    'maxWidth': '200px',
    'overflow': 'hidden',
    'textOverflow': 'ellipsis',
}

TABLE_STYLE_HEADER = {
    'backgroundColor': '#006699',
    'fontWeight': 'bold',
    'color': 'white',
    'textAlign': 'center',
    'fontSize': '11px',
    'padding': '8px',
    'border': '1px solid #ddd'
}

TABLE_STYLE_HEADER_LIGHT = {
    'backgroundColor': '#f8f9fa',
    'fontWeight': 'bold',
    'fontSize': '11px',
    'textAlign': 'center',
    'border': '1px solid #ddd',
    'color': '#495057'
}

# ================== LAYOUT STYLES ==================
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "250px",
    "padding": "20px",
    "backgroundColor": "#f8f9fa",
    "borderRight": "1px solid #dee2e6",
    "overflowY": "auto",
    "zIndex": 1000
}

CONTENT_STYLE = {
    "marginLeft": "260px",
    "marginRight": "10px",
    "padding": "0px"
}

PAGE_CONTENT_STYLE = {
    "padding": "20px"
}

# ================== CARD STYLES ==================
STATS_CARD_STYLE = {
    'width': '98%',
    'padding': '10px',
    'border': '2px solid #0056b3',
    'border-radius': '5px',
    'background-color': '#f7f9fc',
    'margin-bottom': '15px'
}

INFO_CARD_STYLE = {
    'width': '98%',
    'padding': '15px',
    'border': '2px solid #17a2b8',
    'border-radius': '8px',
    'background-color': '#d1ecf1',
    'margin-bottom': '20px'
}

WARNING_CARD_STYLE = {
    'width': '98%',
    'padding': '15px',
    'border': '2px solid #ffc107',
    'border-radius': '8px',
    'background-color': '#fff3cd',
    'margin-bottom': '20px'
}

SUCCESS_CARD_STYLE = {
    'width': '98%',
    'padding': '15px',
    'border': '2px solid #28a745',
    'border-radius': '8px',
    'background-color': '#d4edda',
    'margin-bottom': '20px'
}

# ================== BUTTON STYLES ==================
PRIMARY_BUTTON_STYLE = {
    'background-color': '#0056b3',
    'color': 'white',
    'border': 'none',
    'padding': '10px 20px',
    'font-size': '14px',
    'cursor': 'pointer',
    'border-radius': '5px',
    'margin': '5px'
}

SECONDARY_BUTTON_STYLE = {
    'background-color': '#6c757d',
    'color': 'white',
    'border': 'none',
    'padding': '8px 16px',
    'font-size': '12px',
    'cursor': 'pointer',
    'border-radius': '4px',
    'margin': '3px'
}

SUCCESS_BUTTON_STYLE = {
    'background-color': '#28a745',
    'color': 'white',
    'border': 'none',
    'padding': '10px 20px',
    'font-size': '14px',
    'cursor': 'pointer',
    'border-radius': '5px',
    'margin': '5px'
}

WARNING_BUTTON_STYLE = {
    'background-color': '#ffc107',
    'color': '#212529',
    'border': 'none',
    'padding': '10px 20px',
    'font-size': '14px',
    'cursor': 'pointer',
    'border-radius': '5px',
    'margin': '5px'
}

# ================== COLOR CONSTANTS ==================
COLORS = {
    'primary': '#0056b3',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'muted': '#6c757d'
}

# ================== STATUS COLORS ==================
STATUS_COLORS = {
    'complete': '#28a745',      # Green
    'in_progress': '#ffc107',   # Yellow
    'pending': '#17a2b8',       # Blue
    'not_requested': '#6c757d', # Gray
    'error': '#dc3545',         # Red
    'partial': '#fd7e14'        # Orange
}

# ================== CONDITIONAL STYLING ==================
def get_status_style_conditional():
    """Get conditional styling for status columns"""
    return [
        {
            'if': {
                'filter_query': '{sec_status} contains "Complete" || {sec_status} contains "✅"'
            },
            'backgroundColor': '#d4edda',
            'color': '#155724'
        },
        {
            'if': {
                'filter_query': '{sec_status} contains "Progress" || {sec_status} contains "🔄"'
            },
            'backgroundColor': '#fff3cd',
            'color': '#856404'
        },
        {
            'if': {
                'filter_query': '{sec_status} contains "Not Requested" || {sec_status} contains "⚪"'
            },
            'backgroundColor': '#f8f9fa',
            'color': '#6c757d'
        },
        {
            'if': {
                'filter_query': '{sec_status} contains "Error" || {sec_status} contains "❌"'
            },
            'backgroundColor': '#f8d7da',
            'color': '#721c24'
        }
    ]

# ================== COMMON COLUMN CONFIGURATIONS ==================
SAMPLE_SET_COLUMNS = [
    {"name": "Project", "id": "project"},
    {"name": "Sample Range", "id": "range"},
    {"name": "SIP #", "id": "sip"},
    {"name": "Development Stage", "id": "development_stage"},
    {"name": "Sample Count", "id": "count"},
    {"name": "SEC Status", "id": "sec_status"},
    {"name": "SEC Actions", "id": "sec_actions", "presentation": "markdown"}
]

FB_SAMPLE_COLUMNS = [
    {"name": "Sample #", "id": "sample_number", "editable": False},
    {"name": "Project", "id": "project", "editable": False},
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Dev Stage", "id": "development_stage", "editable": True},
    {"name": "SIP #", "id": "sip_number", "editable": True},
    {"name": "Analyst", "id": "analyst", "editable": True},
    {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa HF", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
    {"name": "SEC Status", "id": "sec_status", "editable": False},
    {"name": "Report", "id": "report_link", "editable": False, "presentation": "markdown"}
]

# ================== EDITABLE FIELDS ==================
EDITABLE_FIELDS = [
    "cell_line", "harvest_date", "development_stage", "hf_octet_titer",
    "hccf_loading_volume", "sip_number", "analyst", "pro_aqa_hf_titer",
    "pro_aqa_e_titer", "proa_eluate_a280_conc", "proa_eluate_volume", "note"
]

# ================== ICON MAPPINGS ==================
ICONS = {
    'dashboard': 'fa-tachometer-alt',
    'samples': 'fa-vial',
    'sample_sets': 'fa-layer-group',
    'add': 'fa-plus',
    'analytics': 'fa-chart-bar',
    'sec': 'fa-microscope',
    'reports': 'fa-chart-line',
    'settings': 'fa-cogs',
    'refresh': 'fa-sync',
    'save': 'fa-save',
    'export': 'fa-download',
    'view': 'fa-eye',
    'edit': 'fa-edit',
    'delete': 'fa-trash',
    'complete': 'fa-check-circle',
    'pending': 'fa-clock',
    'error': 'fa-exclamation-triangle'
}