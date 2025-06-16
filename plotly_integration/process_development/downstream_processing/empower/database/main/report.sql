create table report
(
    report_id           INTEGER
        primary key autoincrement,
    report_name         TEXT,
    project_id          TEXT,
    analysis_type       TEXT,
    sample_type         TEXT,
    selected_samples    TEXT,
    comments            TEXT,
    user_id             TEXT,
    date_created        TEXT,
    selected_result_ids TEXT
);

