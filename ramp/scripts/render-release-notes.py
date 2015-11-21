#!/usr/bin/python

import sys

from ramp import *
from xml.sax.saxutils import escape as escape_html
from pprint import *

tickets_sql = """
select link, key, summary
from tickets
where type in (%s) and resolution = 'Fixed'
order by key
"""

def main():
    db_path = sys.argv[1]
    html_path = sys.argv[2]

    html = render_body(db_path)

    file = open(html_path, "w")
    try:
        file.write(html)
    finally:
        file.close()

def render_body(db_path):
    conn = sqlite3.connect(db_path)

    try:
        lines = list()

        lines.append(render_heading("New Features and Improvements"))
        lines.append(render_tickets(conn, "New Feature", "Improvement"))

        lines.append(render_heading("Bugs Fixed"))
        lines.append(render_tickets(conn, "Bug"))

        lines.append(render_heading("Tasks"))
        lines.append(render_tickets(conn, "Task"))

        return "\n".join(lines)
    finally:
        conn.close()

def render_heading(text):
    return "<h2>%s</h2>" % text

def render_tickets(conn, *types):
    cursor = conn.cursor()
    types_sql = ", ".join(["'%s'" % x for x in types])
    cursor.execute(tickets_sql % types_sql)

    records = cursor.fetchall()

    if not records:
        return "<p><i>None</i></p>"

    lines = list()

    lines.append("<ul>")

    for record in records:
        lines.append(render_item(record))

    lines.append("</ul>")

    return "".join(lines)

def render_item(record):
    args = record[0], escape_html(record[1]), escape_html(record[2])
    return "<li><a href='%s'>%s</a> - %s</li>" % args

if __name__ == "__main__":
    main()
