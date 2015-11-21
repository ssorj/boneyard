from __future__ import division
import time
import inspect

from mint.util import MintDaemonThread
from time import sleep
from update import ObjectUpdate
from random import randrange
from datetime import timedelta, datetime
from bson.code import Code

try:
    from pymongo import Connection
    from pymongo.errors import AutoReconnect
    from pymongo.collection import Collection
    from pymongo.database import Database
    imports_ok = True
except:
    imports_ok = False

import logging

log = logging.getLogger("mint.plumage.session")

UTC_DIFF = datetime.utcnow() - datetime.now() # needed because everything in mongo is UTC

timestamp_mapper = Code("""
               function () {
                    emit({ts:this.ts, st:this.st}, {mem: this.mem, cpu: this.cpu});
               }
               """)

timestamp_reducer = Code("""
                function (key, values) {
                    var memsum = 0;
                    var cpusum = 0;
                      values.forEach(function(doc) {
                           memsum += doc.mem;
                           cpusum += doc.cpu;
                      });
                      return {mem: memsum, cpu: cpusum}; //format of this needs to be same as second param of emit
                }
                """)


class RecordObject(object):
    pass

class PlumageSession(object):
    def __init__(self, app, server_host, server_port):
        self.app = app
        self.server_host = server_host
        self.server_port = server_port
        self.threads = []
        
    def check(self):
        log.info("Checking %s", self)

    def init(self):
        log.info("Initializing %s", self)

    def init_classes(self):
        if not imports_ok:
            return

        # Apply the package filter to the class list
        if len(self.app.classes):
            black_list = set()
            for cls in self.app.classes:
                if cls._package._name in self.app.package_filter:
                    black_list.add(cls)
                else:
                    try:
                        loaders = ClassLoaders()
                        # Here we grab the name of the method to use (should be in rosemary.xml package/class/loading_class)
                        func = getattr(loaders, cls.loading_class, None)
                        func(self, cls)
                    except Exception, e:
                        log.error("No loading function for class %s (%s).  Be sure that the method exists and is defined in rosemary.xml" % (cls._name, str(e)))

            # Update our list, minus the black_list
            self.app.classes.difference_update(black_list)

        else:
            # Generate the package list from the model, minus
            # the package filter
            for pkg in self.app.model._packages:
                if pkg._name not in self.app.package_filter:
                    self.app.packages.add(pkg)
                    loaders = ClassLoaders()
                    for cls in pkg._classes:
                        try:
                            # Here we grab the name of the method to use (should be in rosemary.xml package/class/loading_class)
                            func = getattr(loaders, cls.loading_class, None)
                            func(self, cls)
                        except Exception, e:
                            log.error("No loading function for class %s (%s).  Be sure that the method exists and is defined in rosemary.xml" % (cls._name, str(e)))
    def start(self):
        log.info("Starting %s", self)
        if not imports_ok:
            log.info("!!! Imports failed for pymongo, there will be no data !!!")

        for t in self.threads:
            t.start()

    def stop(self):
        log.info("Stopping %s", self)
        for t in self.threads:
            t.stop()

    def __repr__(self):
        return "%s(%s:%s)" % (self.__class__.__name__, self.server_host, self.server_port)

class ClassLoaders(object):
    ''' method for loading the com.redhat.grid.plumage.OSUtil data from plumage, name is found in rosemary.xml under package/class/loading_class '''
    def OSUtilLoader(self, obj, cls):
        obj.threads.append(CatchUpPlumageOSUtilSessionThread(obj.app, obj.server_host, obj.server_port, cls))
        obj.threads.append(PlumageOSUtilSessionThread(obj.app, obj.server_host, obj.server_port, cls))
        obj.threads.append(CurrentPlumageOSUtilSessionThread(obj.app, obj.server_host, obj.server_port, cls))

    ''' method for loading the com.redhat.grid.plumage.Accountant data from plumage, name is found in rosemary.xml under package/class/loading_class '''        
    def AccountantLoader(self, obj, cls):
        log.debug("AccountLoader called")
        obj.threads.append(CatchupPlumageAccountantSessionThread(obj.app, obj.server_host, obj.server_port, cls))
        obj.threads.append(PlumageAccountantSessionThread(obj.app, obj.server_host, obj.server_port, cls))
        obj.threads.append(CurrentPlumageAccountantSessionThread(obj.app, obj.server_host, obj.server_port, cls))

class PlumageSessionThread(MintDaemonThread):
    def __init__(self, app, server_host, server_port, cls):
        super(PlumageSessionThread, self).__init__(app)
        self.cls = cls
        
        self.server_host = server_host
        self.server_port = server_port

        try:
            self.connection = Connection(server_host, server_port)
        except AutoReconnect:
            self.connection = None
            log.info("%s could not connect to mongo server at %s:%s, "\
                     "autoreconnect is on" % (self.__class__.__name__, 
                                              server_host, 
                                              server_port))
        self.database = None
        self.collection = None

    def _init(self):
        if self.database is None:
            self.database = Database(self.connection, self.cls.database)

        if self.collection is None:
            self.collection = Collection(self.database, self.cls.collection)

    def _check_connection(self):
        # Loop waiting for the server if it's not there.  Autoreconnect
        # will hook us up...
        while not self.stop_requested:
            try:
                if self.connection is None:
                    self.connection = Connection(self.server_host, 
                                                 self.server_port)
                else:
                    self.connection.server_info()
                break
            except AutoReconnect, e:
                log.info("%s waiting for server, %s, sleeping..."\
                             % (self.__class__.__name__, str(e)))
                for i in range(10):
                    sleep(1)
                    if self.stop_requested:
                        break
    

class PlumageAccountantSessionThread(PlumageSessionThread):
    def fillAccountantStats(self, time, temptable, name):
        record = RecordObject()
        record.host= "%s:%s" % (self.connection.host, self.connection.port)
        record.user = name
        record.ts = time - UTC_DIFF
        
        userentry = self.collection.find({'ts':time, 'n':name})[0]
        record.agroup = self.getEntry(userentry, "ag")
        record.prio = self.getEntry(userentry, "prio")
        record.wresused = self.getEntry(userentry, "wru")
        record.resused = self.getEntry(userentry, "ru")
        record.cquota = self.getEntry(userentry, "cq")
        record.equota = self.getEntry(userentry, "eq")
        record.squota = self.getEntry(userentry, "sq")
        record.wausage = self.getEntry(userentry, "au")
        
        return record    
    
    def getEntry(self, item, value):
        result = None
        try:
            result = item[value]
        except:
            result = None
        return result
    
    def run(self):
        while True:
            self._check_connection()
            if self.stop_requested:
                return
    
            try:
                # Make sure we have a database
                self._init()
    
                # We create objects here. Tag them with the right class,
                # probably specified to us from a config option (with a corresponding
                # query specification in the xml)
                (oldest, newest) = self.app.update_thread.get_first_and_last_sample_timestamp(self.cls)
                if oldest is None:
                    # if we have no oldest record (first run), start at "10 min ago" and start loading everything
                    oldest = datetime.now() - timedelta(seconds=600)
                oldest = oldest + UTC_DIFF 
    
                log.info("PlumageAccountantSessionThread--history:  Loading records older than %s" % oldest)
                times = sorted(self.collection.find({"ts": {'$lt': oldest}}).distinct('ts'), reverse=True)
                sample_times = map(lambda i: times[i],filter(lambda i: i%5 == 0,range(len(times))))
    
                for time in sample_times:
                    names = self.collection.find({'ts':time}).distinct('n')
                    for name in names:
                        record = self.fillAccountantStats(time, "history", name)    
                        obj = ObjectUpdate(self.app.model, record, self.cls)
                        self.app.update_thread.enqueue(obj)
    
                log.info("PlumageAccountantSessionThread--history:  run completed")
    
            except Exception, e:
                log.info("%s got exception %s, exiting" % (self.__class__.__name__, str(e)))
            #wake up once a day just in case there has been additional historical items added
            sleep(86400)

class CurrentPlumageAccountantSessionThread(PlumageAccountantSessionThread):
    def run(self):
        while True:
            self._check_connection()
            if self.stop_requested:
                break
            
            # Make sure we have a db
            try:
                self._init()

                (oldest, newest) = self.app.update_thread.get_first_and_last_sample_timestamp(self.cls)
                if newest is not None:            
                    most_recent = max((datetime.now() - timedelta(seconds=600) + UTC_DIFF), (newest + UTC_DIFF))
                else:
                    most_recent = datetime.now() - timedelta(seconds=600) + UTC_DIFF

                log.info("CurrentPlumageAccountantThread--current:  Loading records newer than %s" % most_recent)

                times = sorted(self.collection.find({"ts": {'$gt': most_recent}}).distinct('ts'), reverse=True)
                sample_times = map(lambda i: times[i],filter(lambda i: i%5 == 0,range(len(times))))

                for time in sample_times:
                    names = self.collection.find({'ts':time}).distinct('n')
                    for name in names:
                        record = self.fillAccountantStats(time, "current", name)    
                        obj = ObjectUpdate(self.app.model, record, self.cls)
                        self.app.update_thread.enqueue(obj)

                log.info("CurrentPlumageAccountantThread--current:  pass completed")
            except Exception, e:
                log.info("%s got exception %s, sleeping" % (self.__class__.__name__, str(e)))
            sleep(600)

class CatchupPlumageAccountantSessionThread(PlumageAccountantSessionThread):
    def run(self):
        self._check_connection()
        if self.stop_requested:
            return

        try:
            # Make sure we have a db
            self._init()

            (oldest, newest) = self.app.update_thread.get_first_and_last_sample_timestamp(self.cls)
            if newest is not None:
                log.info("CatchupPlumageAccountantThread: Starting for records newer than %s" % newest)

                times = sorted(self.collection.find({"ts": {'$gt': newest + UTC_DIFF, '$lt': datetime.now() - timedelta(seconds=600) + UTC_DIFF}}).distinct('ts'), reverse=True)
                sample_times = map(lambda i: times[i],filter(lambda i: i%5 == 0,range(len(times))))

                for time in sample_times:
                    names = self.collection.find({'ts':time}).distinct('n')
                    for name in names:
                        record = self.fillAccountantStats(time, "catchup", name)    
                        obj = ObjectUpdate(self.app.model, record, self.cls)
                        self.app.update_thread.enqueue(obj)
                        
                log.info("CatchupPlumageAccountantThread--catch-up:  catch-up run completed for records newer than %s and older than %s" % (newest, datetime.now() - timedelta(seconds=300) + UTC_DIFF))
            else:
                log.info("CatchUpPlumageSessionThread:  Skipping catch-up, no records present (probably first-run)")
        except Exception, e:
            log.info("%s got exception %s, exiting" % (self.__class__.__name__, str(e)))

class PlumageOSUtilSessionThread(PlumageSessionThread):    
    def fillOSUtilStats(self, time, temptable):
        record = RecordObject()
        record.host= "%s:%s" % (self.connection.host, self.connection.port)
        record.total = len(self.collection.find({'ts':time}).distinct('n'))
        record.used = len(self.collection.find({'ts':time,'st':{'$nin':['Unclaimed','Owner']}}).distinct('n'))
        record.unused = len(self.collection.find({'ts':time,'st':'Unclaimed'}).distinct('n'))
        record.owner = len(self.collection.find({'ts':time,'st':'Owner'}).distinct('n'))
        reduced = self.collection.map_reduce(timestamp_mapper, timestamp_reducer, temptable, query={'ts':time,})
        reduced_collection = Collection(self.database,temptable)
        
        result_claimed = reduced_collection.find({'_id.st':'Claimed'})
        result_unclaimed = reduced_collection.find({'_id.st':'Unclaimed'})
        result_owner = reduced_collection.find({'_id.st':'Owner'})
        result_matched = reduced_collection.find({'_id.st':'Matched'})

        record.freemem = self.getStat(result_unclaimed, 'mem')
        record.freecpu = self.getStat(result_unclaimed, 'cpu')       
        record.usedmem = self.getStat(result_claimed, 'mem')
        record.usedcpu = self.getStat(result_claimed, 'cpu')        
        record.availmem = self.getStat(result_claimed, 'mem') + self.getStat(result_unclaimed, 'mem')
        record.availcpu = self.getStat(result_claimed, 'cpu') + self.getStat(result_unclaimed, 'cpu')
        record.totalmem = self.getStat(result_claimed, 'mem') + self.getStat(result_unclaimed, 'mem') + self.getStat(result_owner, 'mem') + self.getStat(result_matched, 'mem')
        record.totalcpu = self.getStat(result_claimed, 'cpu') + self.getStat(result_unclaimed, 'cpu') + self.getStat(result_owner, 'cpu') + self.getStat(result_matched, 'cpu') 
        
        if(record.total != record.owner):
            record.efficiency = (record.used/(record.total-record.owner))*100
        else:
            record.efficiency = 0  
        record.ts = time - UTC_DIFF
        return record
    
    def getStat(self, result_object, item):
        itemcount = 0
        try:
            itemcount = result_object[0]['value'][item]
        except:
            return 0
        return itemcount
        
    def run(self):
        while True:
            self._check_connection()
            if self.stop_requested:
                return
    
            try:
                # Make sure we have a database
                self._init()
    
                # We create objects here. Tag them with the right class,
                # probably specified to us from a config option (with a corresponding
                # query specification in the xml)
                (oldest, newest) = self.app.update_thread.get_first_and_last_sample_timestamp(self.cls)
                if oldest is None:
                    # if we have no oldest record (first run), start at "5 min ago" and start loading everything
                    oldest = datetime.now() - timedelta(seconds=300)
                oldest = oldest + UTC_DIFF 
    
                log.info("PlumageSessionThread--history:  Loading records older than %s" % oldest)
                times = sorted(self.collection.find({"ts": {'$lt': oldest}}).distinct('ts'), reverse=True)
                sample_times = map(lambda i: times[i],filter(lambda i: i%5 == 0,range(len(times))))
    
                for time in sample_times:
                    record = self.fillOSUtilStats(time, "history")
    
                    obj = ObjectUpdate(self.app.model, record, self.cls)
                    self.app.update_thread.enqueue(obj)
    
                log.info("PlumageSessionThread--history:  run completed")
    
            except Exception, e:
                log.info("%s got exception %s, exiting" % (self.__class__.__name__, str(e)))
            #wake up once a day just in case there has been additional historical items added
            sleep(86400)
          
class CurrentPlumageOSUtilSessionThread(PlumageOSUtilSessionThread):
    def run(self):
        while True:
            self._check_connection()
            if self.stop_requested:
                break
            
            # Make sure we have a db
            try:
                self._init()

                (oldest, newest) = self.app.update_thread.get_first_and_last_sample_timestamp(self.cls)
                if newest is not None:            
                    most_recent = max((datetime.now() - timedelta(seconds=300) + UTC_DIFF), (newest + UTC_DIFF))
                else:
                    most_recent = datetime.now() - timedelta(seconds=300) + UTC_DIFF

                log.info("PlumageSessionThread--current:  Loading records newer than %s" % most_recent)

                times = sorted(self.collection.find({"ts": {'$gt': most_recent}}).distinct('ts'), reverse=True)
                sample_times = map(lambda i: times[i],filter(lambda i: i%5 == 0,range(len(times))))

                for time in sample_times:
                    record = self.fillOSUtilStats(time, "current")

                    obj = ObjectUpdate(self.app.model, record, self.cls)
                    self.app.update_thread.enqueue(obj)

                log.info("PlumageSessionThread--current:  pass completed")
            except Exception, e:
                log.info("%s got exception %s, sleeping" % (self.__class__.__name__, str(e)))
            sleep(300)


'''This thread is meant to run once at startup.  It will figure out the newest record in the cumin
   database and then make a pass to load all records from that time forward (up to 5 min ago...those get
   picked-up by the currency thread.
'''            
class CatchUpPlumageOSUtilSessionThread(PlumageOSUtilSessionThread):
    def run(self):
        self._check_connection()
        if self.stop_requested:
            return

        try:
            # Make sure we have a db
            self._init()

            (oldest, newest) = self.app.update_thread.get_first_and_last_sample_timestamp(self.cls)
            if newest is not None:
                log.info("CatchUpPlumageSessionThread: Starting for records newer than %s" % newest)

                times = sorted(self.collection.find({"ts": {'$gt': newest + UTC_DIFF, '$lt': datetime.now() - timedelta(seconds=300) + UTC_DIFF}}).distinct('ts'), reverse=True)
                sample_times = map(lambda i: times[i],filter(lambda i: i%5 == 0,range(len(times))))

                for time in sample_times:
                    record = self.fillOSUtilStats(time, "catchup")

                    obj = ObjectUpdate(self.app.model, record, self.cls)
                    self.app.update_thread.enqueue(obj)
                log.info("CatchUpPlumageSessionThread--catch-up:  catch-up run completed for records newer than %s and older than %s" % (newest, datetime.now() - timedelta(seconds=300) + UTC_DIFF))
            else:
                log.info("CatchUpPlumageSessionThread:  Skipping catch-up, no records present (probably first-run)")
        except Exception, e:
            log.info("%s got exception %s, exiting" % (self.__class__.__name__, str(e)))
