create table akta_result
(
    id                 INTEGER
        primary key autoincrement,
    result_id          TEXT
        unique,
    column_name        TEXT,
    column_volume      TEXT,
    method             TEXT,
    result_path        TEXT,
    date               TEXT,
    user               TEXT,
    sample_id          TEXT,
    run_type           INTEGER,
    scouting_id        INTEGER,
    scouting_run_num   INTEGER,
    group_id           INTEGER,
    system             TEXT,
    source_material_id INTEGER,
    downstream_step_id INTEGER
);

