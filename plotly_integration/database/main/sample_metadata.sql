create table sample_metadata
(
    id                            integer not null
        primary key autoincrement,
    result_id                     integer not null,
    system_name                   text    not null,
    project_name                  text,
    sample_prefix                 text,
    sample_number                 integer,
    sample_suffix                 text,
    sample_type                   text,
    sample_name                   text,
    sample_set_id                 integer,
    sample_set_name               text,
    acquired_by                   text,
    run_time                      real,
    processing_method             text,
    processed_channel_description text,
    injection_volume              real,
    injection_id                  integer,
    column_name                   text,
    column_serial_number          text,
    instrument_method_id          integer,
    instrument_method_name        text,
    date_acquired                 text
);

create unique index sample_metadata_result_id_system_name_6d080668_uniq
    on sample_metadata (result_id, system_name);

