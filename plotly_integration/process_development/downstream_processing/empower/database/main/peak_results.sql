create table peak_results
(
    id                  INTEGER
        primary key autoincrement,
    result_id           INTEGER,
    channel_name        TEXT,
    peak_name           TEXT,
    peak_retention_time REAL,
    peak_start_time     REAL,
    peak_end_time       REAL,
    area                INTEGER,
    percent_area        REAL,
    height              INTEGER,
    asym_at_10          REAL,
    plate_count         REAL,
    res_hh              REAL,
    unique (result_id, peak_retention_time)
);

