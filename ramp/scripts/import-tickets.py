#!/usr/bin/python

import sys

from ramp import *

def main():
    xml_path, db_path = sys.argv[1:3]

    db = TicketDatabase(db_path)
    db.clear()
    db.init()
    db.update(xml_path)

if __name__ == "__main__":
    main()
