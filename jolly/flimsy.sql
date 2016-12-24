select
  '{' || key || ',' || link || '}',
  component,
  version,
  fix_version,
  summary,
  assignee
from tickets 
where resolution = 'Unresolved' and component not like '%Java%'
order by component, assignee;
