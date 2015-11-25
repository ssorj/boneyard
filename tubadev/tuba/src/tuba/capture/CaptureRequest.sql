[load_candidates]
select
  h.program_id,
  h.station_id,
  h.start_time,
  h.end_time,
  h.content_format,
  t.call_sign,
  p.priority as program_priority,
  t.priority as station_priority,
  s.priority as series_priority
from
  showings h
  inner join programs p on h.program_id = p.id
  inner join stations t on h.station_id = t.id
  left outer join series s on p.series_id = s.id
where
  not exists
    (select 1
     from recordings
     where program_sid = p.sid and program_checksum = p.checksum)
  and (s.priority > -1 or p.priority > -1)
  and t.priority > -1
