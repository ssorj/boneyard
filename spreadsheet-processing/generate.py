from model import *
from pencil import *

def people_table(model):
    headings = ("Person",)
    rows = list()

    rows.append(headings)

    for person in model.people:
        rows.append((person.link,))

    return html_table(rows)

def components_table(model):
    headings = "Component", "Upstream", "Downstream"
    rows = list()

    rows.append(headings)

    for component in model.components:
        source = component.source_module
        upstream = list()
        downstream = list()

        if source.upstream_url is not None:
            upstream.append(html_a("Source", source.upstream_url))

        if component.upstream_issues_url is not None:
            upstream.append(html_a("Issues", component.upstream_issues_url))
        
        if source.downstream_url is not None:
            downstream.append(html_a("Source", source.downstream_url))

        if component.downstream_issues_url is not None:
            downstream.append(html_a("Issues", component.downstream_issues_url))

        upstream = ", ".join(upstream)
        downstream = ", ".join(downstream)
            
        rows.append((component, upstream, downstream))

    return html_table(rows)

def load_tasks():
    from xml.etree.ElementTree import XML as _XML
    from zipfile import ZipFile as _ZipFile

    with _ZipFile("data/tasks.ods") as zf:
        xml_data = zf.read("content.xml")
        root = _XML(xml_data)

    ns = {
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    }

    elem = root.find("office:body", ns)
    elem = elem.find("office:spreadsheet", ns)
    elem = elem.find("table:table", ns)

    records = list()
        
    for row in elem.findall("table:table-row", ns):
        cells = row.findall("table:table-cell", ns)
        
        if len(cells) < 6:
            continue

        record = list()
        
        for i in range(6):
            cell = cells[i]
            datum = cell.findtext("text:p", "", ns)

            record.append(datum)
            
        records.append(record)

    return records

def current_tasks_table(model):
    records = load_tasks()

    headings = "Assignee", "Component", "Task", "Size", "Priority", "Jira"
    rows = list()

    rows.append(headings)

    for record in records[1:]:
        assignee, component, summary, size, priority, jira = record

        row = (
            assignee,
            component,
            summary,
            size,
            priority,
            html_a("ENTMQCL-{}".format(jira), "https://issues.jboss.org/browse/ENTMQCL-{}".format(jira))
        )            
        
        rows.append(row)

    return html_table(rows)

small = "Small"
medium = "Medium"
large = "Large"

low = "Low"
normal = "Normal"
high = "High"
