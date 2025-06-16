create table django_plotly_dash_statelessapp
(
    id       integer      not null
        primary key autoincrement,
    app_name varchar(100) not null
        unique,
    slug     varchar(110) not null
        unique
);

