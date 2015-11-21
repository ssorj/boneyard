from collections import deque
from qmf.console import *
from threading import Lock

from util import *

class BasilModel(object):
    def __init__(self):
        super(BasilModel, self).__init__()

        self.broker_urls = set()

        self.console = BasilConsole(self)
        self.session = Session(self.console, manageConnections=True)

        self.lock = Lock()

        self.packages = set()
        self.classes_by_package = defaultdict(dict)
        self.objects_by_class = defaultdict(dict)
        self.objects_by_id = dict()
        self.stats_by_id = defaultdict(StatsRecord)

    def add_broker_url(self, url):
        self.broker_urls.add(url)

    def init(self):
        pass

    def start(self):
        for url in self.broker_urls:
            self.session.addBroker(url)

    def stop(self):
        # XXX hack necessary for shutdown; bug rafi

        for url in self.broker_urls:
            self.session.delBroker(url)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.session)

class BasilConsole(Console):
    def __init__(self, model):
        #Console.__init__(self)
        #super(BasilConsole, self).__init__()

        self.model = model

    def newPackage(self, name):
        self.model.lock.acquire()

        try:
            self.model.packages.add(name)
        finally:
            self.model.lock.release()

    def newClass(self, kind, classKey):
        if kind == 2:
            return # XXX for now, drop events

        self.model.lock.acquire()

        try:
            pkgid = classKey.getPackageName()
            classes = self.model.classes_by_package[pkgid]
            classes[classKey.getHashString()] = classKey
        finally:
            self.model.lock.release()

    def objectProps(self, broker, obj):
        self.model.lock.acquire()

        try:
            clsid = obj.getClassKey().getHashString()
            objs = self.model.objects_by_class[clsid]
            objs[str(obj.getObjectId())] = obj

            self.model.objects_by_id[str(obj.getObjectId())] = obj
        finally:
            self.model.lock.release()

    def objectStats(self, broker, obj):
        self.model.lock.acquire()

        try:
            objid = str(obj.getObjectId())
            stats = self.model.stats_by_id[objid]

            for stat in obj.getStatistics():
                name = stat[0].name
                value = stat[1]

                values = stats[name]
                values.append(value)

                if len(values) > 10:
                    values.popleft()
        finally:
            self.model.lock.release()

class StatsRecord(defaultdict):
    def __init__(self):
        super(StatsRecord, self).__init__(deque)
