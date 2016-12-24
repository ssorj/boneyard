#!/usr/bin/python

import sys
import sqlite3
import os

from xml.etree.ElementTree import *

class TicketDatabase(object):
    def __init__(self, path):
        self.path = path

    def init(self):
        columns = list()

        for name in TicketRecord._fields:
            field_type = TicketRecord._field_types.get(name, unicode)
            column_type = "text"

            if field_type == int:
                column_type = "integer"

            column = "%s %s" % (name, column_type)

            columns.append(column)

        ddl = "create table tickets (%s)" % ", ".join(columns)
        conn = sqlite3.connect(self.path)
        
        try:
            cursor = conn.cursor()
            cursor.execute(ddl)
        finally:
            conn.close()

    def update(self, xml_path):
        file = open(xml_path)

        try:
            tree = ElementTree()
            tree.parse(file)
        finally:
            file.close()

        root = tree.getroot()
        channel = root.find("channel")

        conn = sqlite3.connect(self.path)

        try:
            cursor = conn.cursor()

            for elem in channel.findall("item"):
                record = TicketRecord()
                record.parse(elem)
                record.insert(cursor)

                conn.commit()
        finally:
            conn.close()

    def clear(self):
        if os.path.exists(self.path):
            os.remove(self.path)

class TicketRecord(object):
    _fields = {
        "key": "key/#",
        "component": "component/#",
        "version": "version/#",
        "summary": "summary/#",
        "link": "link/#",
        "fix_version": "fixVersion/#",
        "type_id": "type/@id",
        "type": "type/#",
        "assignee_username": "assignee/@username",
        "assignee": "assignee/#",
        "reporter_username": "reporter/@username",
        "reporter": "reporter/#",
        "status_id": "status/@id",
        "status": "status/#",
        "priority_id": "priority/@id",
        "priority": "priority/#",
        "resolution_id": "resolution/@id",
        "resolution": "resolution/#",
        }

    _field_types = {
        "type_id": int,
        "status_id": int,
        "priority_id": int,
        "resolution_id": int,
        }

    def __init__(self):
        for name in self._fields:
            setattr(self, name, None)

    def parse(self, elem):
        for name in self._fields:
            value = self.get_value(elem, self._fields[name])

            field_type = self._field_types.get(name, unicode)

            if value is not None:
                value = field_type(value)

            setattr(self, name, value)

    def get_value(self, elem, path):
        tokens = path.split("/")
        child = elem

        for token in tokens:
            if child is None:
                return

            if token == "#":
                return child.text

            if token.startswith("@"):
                return child.attrib[token[1:]]
            
            child = child.find(token)

    def insert(self, cursor):
        fields = sorted(self._fields)
        columns = ", ".join(fields)
        values = ", ".join("?" * len(fields))
        args = [getattr(self, x) for x in fields]

        dml = "insert into tickets (%s) values (%s)" % (columns, values)

        #print dml, args

        cursor.execute(dml, args)

def main():
    xml_path = sys.argv[1]
    db_path = sys.argv[2]

    db = TicketDatabase(db_path)
    db.clear()
    db.init()
    db.update(xml_path)

if __name__ == "__main__":
    main()
