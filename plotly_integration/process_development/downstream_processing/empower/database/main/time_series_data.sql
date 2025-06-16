create table time_series_data
(
    id          INTEGER
        primary key autoincrement,
    result_id   INTEGER,
    system_name TEXT,
    time        REAL,
    channel_1   REAL,
    channel_2   REAL,
    channel_3   REAL,
    unique (result_id, time)
);

