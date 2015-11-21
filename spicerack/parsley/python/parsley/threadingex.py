import os
import sys

from threading import *

def print_threads(writer=sys.stdout):
    row = "%-28s  %-36s  %-18s  %-8s  %-8s  %s"

    writer.write(row % ("Class", "Name", "Ident", "Alive", "Daemon", ""))
    writer.write(os.linesep)
    writer.write("-" * 120)
    writer.write(os.linesep)

    for thread in sorted(enumerate()):
        cls = thread.__class__.__name__
        name = thread.name
        ident = thread.ident
        alive = thread.is_alive()
        daemon = thread.daemon
        extra = ""
        #extra = thread._Thread__target

        writer.write(row % (cls, name, ident, alive, daemon, extra))
        writer.write(os.linesep)
