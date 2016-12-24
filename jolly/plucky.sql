.width 10 4 4

select
  key,
  version,
  fix_version,
  summary,
  assignee
from tickets 
where 
  resolution = 'Unresolved'
  and component is 'C++ Broker'
  and (fix_version is null or fix_version < '0.9')
order by component, assignee;


