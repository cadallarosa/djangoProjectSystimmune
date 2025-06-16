create table akta_scouting_list
(
    scouting_id            integer      not null
        primary key autoincrement,
    total_num_of_scoutings bigint       not null,
    run_scouting           bigint       not null,
    run                    bigint       not null,
    scouting               bool         not null,
    variable               text         not null,
    block                  varchar(255) not null,
    name                   varchar(255) not null,
    unit                   varchar(255) not null,
    value                  real         not null
);

