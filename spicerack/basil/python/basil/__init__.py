import mllib, qpid, new
from qpid.datatypes import uuid4
from string import Template
from qpid.management import managementChannel, managementClient
from qpid.util import connect
from qpid.connection import Connection
from threading import Lock

from util import *

class OldBasilModel(object):
    def __init__(self, spec_path):
        self.spec = qpid.spec.load(spec_path)

        self.connections = dict()
        self.packages = list()

        self.method_sequence = 1
        self.method_calls = dict() # seq => (object, name, callback, kwargs)

        self.lock = Lock()

    def on_schema(self, conn, class_info, configs, metrics, methods, events):
        self.lock.acquire()
        try:
            package = self.get_package(class_info)
            package.on_schema(conn, class_info,
                              configs, metrics, methods, events)
        finally:
            self.lock.release()

    def on_props(self, conn, class_info, values, timestamps):
        self.lock.acquire()
        try:
            package = self.get_package(class_info)
            package.on_props(conn, class_info, values, timestamps)
        finally:
            self.lock.release()

    def on_stats(self, conn, class_info, values, timestamps):
        self.lock.acquire()
        try:
            package = self.get_package(class_info)
            package.on_stats(conn, class_info, values, timestamps)
        finally:
            self.lock.release()

    def on_callback(self, conn, seq, status_code, status_text, args):
        self.lock.acquire()
        try:
            object, name, callback, kwargs = self.method_calls.pop(seq)
        finally:
            self.lock.release()

        if callback:
            callback(status_code, status_text, args)
        else:
            print object, name, "->", status_code, status_text, args

    def get_package(self, class_info):
        name = class_info[0].replace(".", "_")

        try:
            package = getattr(self, name)
        except AttributeError:
            package = BasilPackage(self, name)
            self.packages.append(package)
            setattr(self, name, package)

        return package

class BasilPackage(object):
    def __init__(self, model, name):
        self.model = model
        self.name = name

        self.classes = list()

    def on_schema(self, conn, class_info, configs, metrics, methods, events):
        cls = self.get_class(class_info)
        cls.on_schema(conn, class_info, configs, metrics, methods, events)

    def on_props(self, conn, class_info, values, timestamps):
        cls = self.get_class(class_info)
        cls.on_props(conn, class_info, values, timestamps)

    def on_stats(self, conn, class_info, values, timestamps):
        cls = self.get_class(class_info)
        cls.on_stats(conn, class_info, values, timestamps)

    def get_class(self, class_info):
        name = class_info[1]
        
        try:
            cls = getattr(self, name)
        except AttributeError:
            cls = BasilClass(self, name)
            self.classes.append(cls)
            setattr(self, name, cls)

        return cls

    def __repr__(self):
        return self.name

class BasilClass(object):
    def __init__(self, package, name):
        self.package = package
        self.name = name

        self.objects = list()
        self.objects_by_composite_id = dict()

        attrs = dict()
        attrs["basil_model"] = self.package.model
        attrs["basil_package"] = self.package
        attrs["basil_class"] = self
        self.python_class = type(str(name), (BasilObject,), attrs)

    def on_schema(self, conn, class_info, configs, metrics, methods, events):
        for spec in configs:
            setattr(self.python_class, spec[0], None)

        for spec in metrics:
            setattr(self.python_class, spec[0], None)

        for name in methods:
            def meth(this, callback=None, **kwargs):
                this.basil_call(name, callback, **kwargs)
            setattr(self.python_class, name, meth)

        for spec in events:
            pass

    def on_props(self, conn, class_info, values, timestamps):
        id = self.get_object_id(values)
        object = self.get_object(class_info, conn.broker_id, id)

        for name, value in values:
            setattr(object, name, value)

    def on_stats(self, conn, class_info, values, timestamps):
        id = self.get_object_id(values)
        object = self.get_object(class_info, conn.broker_id, id)

        for name, value in values:
            setattr(object, name, value)

    def get_object_id(self, values):
        for name, value in values:
            if name == "id" and value is not None:
                return value

        raise Exception("ID not found")

    def get_object(self, class_info, broker_id, id):
        try:
            object = self.objects_by_composite_id[(broker_id, id)]
        except KeyError:
            object = self.python_class(class_info, broker_id, id)
            self.objects.append(object)
            self.objects_by_composite_id[(broker_id, id)] = object

        return object

    def __repr__(self):
        return self.name

class BasilObject(object):
    def __init__(self, class_info, broker_id, object_id):
        self.basil_class_info = class_info
        self.basil_broker_id = broker_id
        self.basil_object_id = object_id

    def basil_call(self, name, callback, **kwargs):
        model = self.basil_model
        model.lock.acquire()
        try:
            model.method_sequence += 1
            seq = model.method_sequence
        finally:
            model.lock.release()

        conn = model.connections[self.basil_broker_id]
        client, chan = conn.mclient, conn.chan

        model.method_calls[seq] = (self, name, callback, kwargs)

        client.method(chan, seq, self.basil_object_id, self.basil_class_info,
                      name, kwargs)
        
    def __repr__(self):
        return "%r-%r" % (self.basil_broker_id, self.basil_object_id)

class BasilConnection(object):
    def __init__(self, model, host, port):
        self.model = model
        self.host = host
        self.port = port
        self.broker_id = "%s:%i" % (self.host, self.port)

        self.conn = Connection(connect(host, port), self.model.spec)

        self.mclient = managementClient(self.model.spec,
                                        None, 
                                        self.model.on_props,
                                        self.model.on_stats,
                                        self.model.on_callback)
        self.mclient.schemaListener(self.model.on_schema)

        self.chan = None

        self.model.connections[self.broker_id] = self

    def open(self):
        self.conn.start()
        self.chan = self.mclient.addChannel \
            (self.conn.session(str(uuid4())), self)

    def close(self):
        self.mclient.removeChannel(self.chan)
        #self.client.stop()
