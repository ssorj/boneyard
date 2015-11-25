[standard_abbreviations]
seq -> sequence
idx -> index
fk -> foreign key constraint
pk -> primary key constraint
uq -> unique constraint
ck -> check constraint
prg -> programs
srq -> series_requests
prq -> program_requests
rec -> recordings
srs -> series
shg -> showings
stn -> stations
enc -> encodings

[create]
set property "sql.enforce_strict_size" true;

create sequence series_seq as bigint start with 1;

create table series (
       id             bigint not null,
       sid            varchar(50) not null,
       title          varchar(200) not null,
       priority       integer not null,
       constraint srs_pk primary key (id),
       constraint srs_sid_uq unique (sid)
);

create sequence programs_seq as bigint start with 1;

create table programs (
       id             bigint not null,
       sid            varchar(50) not null,
       series_id      bigint,
       title          varchar(200) not null,
       subtitle       varchar(200),
       description    varchar(500),
       original_air_date bigint,
       checksum       char(40) not null,
       priority       integer not null,
       constraint prg_pk primary key (id),
       constraint prg_sid_uq unique (sid),
       constraint prg_series_id_fk
           foreign key (series_id) references series (id)
);

create index programs_checksum_idx on programs (checksum);

create sequence stations_seq as bigint start with 1;

create table stations (
       id             bigint not null,
       sid            varchar(50) not null,
       call_sign      varchar(50) not null,
       fcc_channel    varchar(50) not null,
       transport_format varchar(10),
       priority       integer not null,
       constraint stn_pk primary key (id),
       constraint stn_sid_uq unique (sid),
       constraint stn_call_sign_uq unique (call_sign)
);

create table showings (
       program_id     bigint not null,
       station_id     bigint not null,
       start_time     bigint not null,
       end_time       bigint not null,
       content_format varchar(10),
       constraint shg_program_id_fk
           foreign key (program_id) references programs (id),
       constraint shg_station_id_fk
           foreign key (station_id) references stations (id),
       constraint shg_start_time_station_id_uq
           unique (start_time, station_id)
);

create sequence recordings_seq as bigint start with 1;

create table recordings (
       id             bigint not null,
       file           varchar(400) not null,
       title          varchar(200),
       subtitle       varchar(200),
       description    varchar(500),
       original_air_date bigint,
       program_sid    varchar(50),
       program_checksum char(40),
       call_sign      varchar(10) not null,
       start_time     bigint not null,
       end_time       bigint not null,
       transport_format varchar(10),
       content_format varchar(10),
       constraint rec_start_time_call_sign_uq
           unique (start_time, call_sign),
       constraint rec_file_uq unique (file),
       constraint rec_pk primary key (id)
);

create sequence encodings_seq as bigint start with 1;

create table encodings (
       id             bigint not null,
       recording_id   bigint not null,
       filename       varchar(400) not null,
       constraint enc_recording_id_fk
           foreign key (recording_id) references recordings (id),
       constraint enc_pk primary key (id)
);

[drop]
drop sequence encodings_seq;
drop table encodings;
drop sequence recordings_seq;
drop table recordings;
drop table showings;
drop sequence stations_seq;
drop table stations;
drop index programs_checksum_idx;
drop sequence programs_seq;
drop table programs;
drop sequence series_seq;
drop table series;
