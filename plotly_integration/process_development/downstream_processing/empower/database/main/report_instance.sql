create table report_instance
(
    report_instance_id INTEGER
        primary key autoincrement,
    exclusions         TEXT,
    report_id          INTEGER
);

