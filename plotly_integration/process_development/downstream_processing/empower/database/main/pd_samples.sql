create table pd_samples
(
    id                    integer      not null
        primary key autoincrement,
    result_id             integer      not null,
    pd_number             varchar(255) not null,
    sample_volume_ul      real         not null,
    identifier            varchar(255) not null,
    description_volume    text         not null,
    a280_date             date,
    concentration_mg_ml   real,
    sec_date              date,
    hmw_percentage        real,
    mp_percentage         real,
    lmw_percentage        real,
    sec_total_area        real,
    sec_injection_ug      real,
    sec_dilution          real,
    sec_load_volume_ul    real,
    hplc_proa_titer_mg_ml real,
    hcp_ppm               real,
    proa_ppm              real,
    dna_ppm               real,
    akta_fraction_id      varchar(255)
);

