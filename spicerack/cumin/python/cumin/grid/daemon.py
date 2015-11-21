from cumin.objectframe import *
from cumin.objectselector import *

class DaemonFrameTask(ObjectFrameTask):
    def get_master(self, system_name, invoc):
        cursor = self.app.database.get_read_cursor()

        cls = self.app.model.com_redhat_grid.Master
        master = cls.get_object(cursor, System=system_name)

        if not master:
            invoc.exception = Exception("Master daemon not running")
            invoc.status = invoc.FAILED
            invoc.end()

        return master

class DaemonStart(DaemonFrameTask):
    def __init__(self, app, frame, target):
        super(DaemonStart, self).__init__(app, frame)

        self.target = target

        self.name = "%s_%s" % (self.name, self.target)

    def get_title(self, session):
        return "Start"

    def do_invoke(self, invoc, daemon):
        system_name = daemon.System

        master = self.get_master(system_name, invoc)
        if master:
            self.app.remote.start(master, self.target, invoc.make_callback())

class DaemonStop(DaemonFrameTask):
    def __init__(self, app, frame, target):
        super(DaemonStop, self).__init__(app, frame)

        self.target = target

        self.name = "%s_%s" % (self.name, self.target)

    def get_title(self, session):
        return "Stop"

    def do_invoke(self, invoc, daemon):
        system_name = daemon.System

        master = self.get_master(system_name, invoc)
        if master:
            self.app.remote.stop(master, self.target, invoc.make_callback())

class DaemonSelectorTask(ObjectSelectorTask):
    def get_master(self, system_name, invoc):
        cursor = self.app.database.get_read_cursor()
    
        cls = self.app.model.com_redhat_grid.Master
        master = cls.get_object(cursor, System=system_name)
    
        if not master:
            invoc.exception = Exception("Master daemon not running")
            invoc.status = invoc.FAILED
            invoc.end()
    
        return master

class DaemonSelectionStart(DaemonSelectorTask):
    def __init__(self, app, selector, target):
        super(DaemonSelectionStart, self).__init__(app, selector)

        self.target = target

        self.name = "%s_%s" % (self.name, self.target)

    def get_title(self, session):
        return "Start"

    def do_invoke(self, invoc, daemon):
        system_name = daemon.System

        master = self.get_master(system_name, invoc)
        if master:
            self.app.remote.start(master, self.target, invoc.make_callback())

class DaemonSelectionStop(DaemonSelectorTask):
    def __init__(self, app, selector, target):
        super(DaemonSelectionStop, self).__init__(app, selector)

        cls = app.model.com_redhat_grid.Master

        self.target = target

        self.name = "%s_%s" % (self.name, self.target)

    def get_title(self, session):
        return "Stop"

    def do_invoke(self, invoc, daemon):
        system_name = daemon.System

        master = self.get_master(system_name, invoc)
        if master:
            self.app.remote.stop(master, self.target, invoc.make_callback())
