create table django_plotly_dash_dashapp
(
    id               integer      not null
        primary key autoincrement,
    instance_name    varchar(100) not null
        unique,
    slug             varchar(110) not null
        unique,
    base_state       text         not null,
    creation         datetime     not null,
    "update"         datetime     not null,
    save_on_change   bool         not null,
    stateless_app_id integer      not null
        references django_plotly_dash_statelessapp
            deferrable initially deferred
);

create index django_plotly_dash_dashapp_stateless_app_id_220444de
    on django_plotly_dash_dashapp (stateless_app_id);

