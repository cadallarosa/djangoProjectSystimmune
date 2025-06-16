TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "2px 4px",
    "fontSize": "11px",
    "border": "1px solid #ddd",
    "minWidth": "100px",
    "width": "100px",
    "maxWidth": "200px",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#006699",
    "fontWeight": "bold",
    "color": "white",
    "textAlign": "center",
    "fontSize": "11px",
    "padding": "2px 4px"
}

UP_SAMPLE_FIELDS = [
    {"name": "Project", "id": "project", "editable": False},
    # {"name": "Experiment #", "id": "experiment_number", "editable": True},
    {"name": "Sample #", "id": "sample_number", "editable": False},
    # {"name": "Day", "id": "culture_duration", "editable": True},
    {"name": "Clone", "id": "cell_line", "editable": True},
    # {"name": "Vessel Type", "id": "vessel_type", "editable": True},
    {"name": "SIP #", "id": "sip_number", "editable": True},
    {"name": "Development Stage", "id": "development_stage", "editable": True},
    {"name": "Analyst", "id": "analyst", "editable": True},
    {"name": "Harvest Date (YYYY-MM-DD)", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Unifi #", "id": "unifi_number", "editable": True},
    # {"name": "Titer Comment", "id": "titer_comment", "editable": True},
    {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa Eluate Titer", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
    {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
    {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
    {"name": "Eluate Volume", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
    # {"name": "ProA Recovery", "id": "proa_recovery", "editable": True, "type": "numeric"},
    {"name": "ProAqa Recovery", "id": "fast_pro_a_recovery", "editable": False, "type": "numeric"},
    {"name": "A280 Recovery", "id": "purification_recovery_a280", "editable": False, "type": "numeric"},
    # {"name": "Column Size", "id": "proa_column_size", "editable": True, "type": "numeric"},
    # {"name": "Column ID", "id": "column_id", "editable": True},
    {"name": "Note", "id": "note", "editable": True},
    {"name": "Report Link", "id": "report_link", "editable": False, "presentation": "markdown"}

]

FIELD_IDS = [f["id"] for f in UP_SAMPLE_FIELDS]
EDITABLE_FIELDS = [f["id"] for f in UP_SAMPLE_FIELDS if
                   f["editable"] and f["id"] not in ("sample_number", "report_link")]
NON_EDITABLE_FIELDS = [f["id"] for f in UP_SAMPLE_FIELDS if not f["editable"]]


SEC_COLUMNS = [
    {"name": "Sample Name", "id": "sample_name"},
    {"name": "Result ID", "id": "result_id"},
    {"name": "Date Acquired", "id": "date_acquired"},
    {"name": "Column Name", "id": "column_name"},
    {"name": "Sample Set Name", "id": "sample_set_name"}
]