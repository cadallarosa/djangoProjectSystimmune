create table project_information
(
    id                       SERIAL
        primary key,
    protein                  TEXT not null,
    project                  TEXT not null,
    project_description      TEXT,
    molecule_type            TEXT,
    description              TEXT,
    purifications            TEXT,
    plasmids                 TEXT,
    plasmid_description      TEXT,
    tags                     TEXT,
    transfections            TEXT,
    titer                    FLOAT,
    protein_concentration    FLOAT,
    nanodrop_e1              FLOAT,
    molecular_weight         FLOAT,
    percent_poi              FLOAT,
    pi                       FLOAT,
    latest_purification_date DATE,
    purified                 BOOLEAN default FALSE
);

