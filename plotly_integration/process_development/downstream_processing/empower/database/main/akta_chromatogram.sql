create table akta_chromatogram
(
    id                 INTEGER
        primary key autoincrement,
    result_id          TEXT,
    ml                 REAL,
    uv_1_280           REAL,
    uv_2_0             REAL,
    uv_3_0             REAL,
    cond               REAL,
    conc_b             REAL,
    pH                 REAL,
    system_flow        REAL,
    system_linear_flow REAL,
    system_pressure    REAL,
    cond_temp          REAL,
    sample_flow        REAL,
    sample_linear_flow REAL,
    sample_pressure    REAL,
    preC_pressure      REAL,
    deltaC_pressure    REAL,
    postC_pressure     REAL,
    frac_temp          REAL
);

