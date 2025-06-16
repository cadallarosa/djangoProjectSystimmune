create table akta_method_information
(
    id                 integer      not null
        primary key autoincrement,
    method_name        varchar(255) not null,
    last_saved         datetime     not null,
    created_by_user    varchar(255) not null,
    method_notes       text         not null,
    result_name        varchar(255) not null,
    start_notes        text         not null,
    scouting           bigint       not null,
    created_for_system varchar(255) not null
);

