create table results
(
    result_id            INTEGER
        primary key autoincrement,
    system_name          TEXT,
    project_name         INTEGER,
    sample_set_id        INTEGER,
    sample_set_name      TEXT,
    aquired_by           TEXT,
    column_serial_number TEXT,
    new_column           INTEGER
);

