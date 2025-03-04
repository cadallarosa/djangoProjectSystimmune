create table chrom_metadata
(
    id              INTEGER
        primary key autoincrement,
    result_id       INTEGER,
    system_name     TEXT,
    sample_name     TEXT,
    sample_set_name TEXT,
    sample_set_id   INTEGER,
    channel_1       TEXT,
    channel_2       TEXT,
    channel_3       TEXT,
    unique (result_id, system_name)
);

