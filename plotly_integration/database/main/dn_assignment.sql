create table dn_assignment
(
    id                     integer      not null
        primary key autoincrement,
    dn                     varchar(255) not null,
    project_id             varchar(255) not null,
    study_name             varchar(255) not null,
    description_of_purpose text         not null,
    load_volume            real         not null,
    notes                  text         not null
);

