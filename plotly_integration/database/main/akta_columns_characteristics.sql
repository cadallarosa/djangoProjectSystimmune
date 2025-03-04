create table akta_columns_characteristics
(
    column_id             integer      not null
        primary key autoincrement,
    column_type           varchar(255) not null,
    technique             varchar(255) not null,
    column_volume         real         not null,
    diameter              real         not null,
    bed_height            real         not null,
    resin                 varchar(255) not null,
    alias                 varchar(255) not null,
    asymmetry             real         not null,
    plates_per_meter      real         not null,
    HETP                  real         not null,
    num_cycles            bigint       not null,
    avg_starting_pressure real         not null
);

