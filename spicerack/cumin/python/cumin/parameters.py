from wooly import *
from mint import *

from model import Pool
#from model import Job

class UserAttribute(Attribute):
    def get(self, session):
        login = session.client_session.attributes["login_session"]

        return login.user

class CuminClassParameter(Parameter):
    def do_unmarshal(self, string):
        return getattr(self.app.model, string, None)

    def do_marshal(self, cls):
        return cls.cumin_name

class RosemaryObjectParameter(Parameter):
    def __init__(self, app, name, cls):
        super(RosemaryObjectParameter, self).__init__(app, name)

        self.cls = cls

    def do_unmarshal(self, string):
        cursor = self.app.database.get_read_cursor()
        return self.cls.get_object_by_id(cursor, int(string))

    def do_marshal(self, obj):
        return str(obj._id)

class ObjectAttribute(Attribute):
    def __init__(self, widget, name, cls, id):
        super(ObjectAttribute, self).__init__(widget, name)

        assert isinstance(cls, RosemaryClass), cls

        self.cls = cls
        self.id = id

    def process(self, session):
        id = self.id.get(session)

        if id:
            obj = self.cls.get_object_by_id(session.cursor, id)
            self.set(session, obj)

    def get_default(self, session):
        self.process(session)
        obj = session.get(self.path)
        return obj

class YoungestAttribute(Attribute):
    def __init__(self, app, name, cls):
        super(YoungestAttribute, self).__init__(app, name)
        self.cls = cls

    def get(self, session):
        val = super(YoungestAttribute, self).get(session)
        if not val:
            val = self.app.model.find_youngest(self.cls, session.cursor)
            if val:
                self.set(session, val)
        return val

class BrokerGroupParameter(Parameter):
    def do_unmarshal(self, string):
        if string == "__none__":
            object = None
        else:
            try:
                object = BrokerGroup.get(int(string))
            except SQLObjectNotFound:
                object = None

        return object

    def do_marshal(self, group):
        return str(group.id)

class NewBrokerGroupParameter(Parameter):
    def do_unmarshal(self, string):
        id = int(string)
        cls = self.app.model.com_redhat_cumin_messaging.BrokerGroup

        cursor = self.app.database.get_read_cursor()

        return cls.get_object_by_id(cursor, id)

class BrokerParameter(Parameter):
    def do_unmarshal(self, string):
        return Broker.get(int(string))

    def do_marshal(self, broker):
        return str(broker.id)

class ExchangeParameter(Parameter):
    def do_unmarshal(self, string):
        return Exchange.get(int(string))

    def do_marshal(self, exchange):
        return str(exchange.id)

class JobParameter(Parameter):
    def do_unmarshal(self, id):
        return Job.get(int(id))

    def do_marshal(self, job):
        return str(job.id)

class LinkParameter(Parameter):
    def do_unmarshal(self, string):
        return Link.get(int(string))

    def do_marshal(self, link):
        return str(link.id)

class PeerParameter(LinkParameter):
    pass

# XXX marked for death
class PeerParameter(LinkParameter):
    pass

class QueueParameter(Parameter):
    def do_unmarshal(self, string):
        return Queue.get(int(string))

    def do_marshal(self, queue):
        return str(queue.id)

class RouteParameter(Parameter):
    def do_unmarshal(self, string):
        return Bridge.get(int(string))

    def do_marshal(self, route):
        return str(route.id)

class NegotiatorParameter(Parameter):
    def do_unmarshal(self, string):
        return Negotiator.get(int(string))

    def do_marshal(self, neg):
        return str(neg.id)
