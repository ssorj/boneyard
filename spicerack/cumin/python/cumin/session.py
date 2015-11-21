from model import *
from util import *
from mint.util import make_agent_id

from qmf.console import Console, Session, ObjectId
from rosemary.model import RosemaryObject
from sage.util import get_sasl_mechanisms

log = logging.getLogger("cumin.session")

class CuminSession(object):
    def __init__(self, app, broker_uris):
        self.app = app
        self.broker_uris = broker_uris

        self.qmf_session = None
        self.qmf_brokers = list()
        self.qmf_agents = dict()

        # int seq => callable
        self.outstanding_method_calls = dict()

        self.lock = Lock()

    def add_broker(self, uri):
        mechs = get_sasl_mechanisms(uri, self.app.sasl_mech_list)
        uri_without_password = uri[uri.rfind("@") + 1:]
        log.info("Adding QMF broker at %s with mech_list %s", uri_without_password, mechs)

        assert self.qmf_session

        qmf_broker = self.qmf_session.addBroker(uri,mechanisms=mechs)

        self.qmf_brokers.append(qmf_broker)

    def check(self):
        log.info("Checking %s", self)

    def init(self):
        uris_without_password = [x[x.rfind("@")+1:]  for x in self.broker_uris]
        log.info("Initializing %s", uris_without_password)

    def start(self):
        log.info("Starting %s", self)

        assert self.qmf_session is None

        self.qmf_session = Session(CuminConsole(self),
                                   manageConnections=True,
                                   rcvObjects=False,
                                   rcvEvents=False,
                                   rcvHeartbeats=False)

        for uri in self.broker_uris:
            self.add_broker(uri)

    def stop(self):
        log.info("Stopping %s", self)

        for qmf_broker in self.qmf_brokers:
            self.qmf_session.delBroker(qmf_broker)

    def get_agent(self, agent_id):
        self.lock.acquire()
        try:
            return self.qmf_agents.get(agent_id)
        finally:
            self.lock.release()

    def call_method(self, callback, obj, name, args):
        assert isinstance(obj, RosemaryObject)

        for i in range(10):
            agent = self.get_agent(obj._qmf_agent_id)

            if agent:
                break

            sleep(1)

        if not agent:
            raise Exception("Agent '%s' is unknown" % obj._qmf_agent_id)

        if obj._qmf_object_id.isdigit():
            # Translate v1 object ids

            if obj._class is self.app.model.org_apache_qpid_broker.Queue:
                # A very special workaround for queue keys

                key = obj.name
            else:
                key_args = [str(getattr(obj, x.name))
                            for x in obj._class._attributes
                            if x.index and not x.references]
                key = ",".join(key_args)

            id_args = (obj._class._package._name, obj._class._name.lower(), key)

            object_id = ":".join(id_args)
        else:
            object_id = obj._qmf_object_id

        oid = ObjectId({"_agent_name": obj._qmf_agent_id,
                        "_object_name": object_id})

        qmf_objs = agent.getObjects(_objectId=oid)

        try:
            qmf_obj = qmf_objs[0]
        except IndexError:
            raise Exception("Object '%s' is unknown" % object_id)

        self.lock.acquire()
        try:
            seq = qmf_obj._invoke(name, args, {"_async": True})

            assert seq is not None

            self.outstanding_method_calls[seq] = callback

            return seq
        finally:
            self.lock.release()

    def __repr__(self):
        uris_without_password = [x[x.rfind("@")+1:]  for x in self.broker_uris]
        return "%s(%s)" % (self.__class__.__name__, uris_without_password)

class CuminConsole(Console):
    def __init__(self, session):
        self.session = session

    def brokerConnected(self, broker):
        log.info("Broker connected %s:%s", broker.host, broker.port)

    def brokerConnectionFailed(self, broker):
        log.info("Broker connection failed %s:%s", broker.host, broker.port)

    def brokerDisconnected(self, broker):
        log.info("Broker disconnected %s:%s", broker.host, broker.port)

    def newPackage(self, name):
        log.debug("New package %s", name)

    def newClass(self, kind, classKey):
        log.debug("New class %s", classKey)

    def newAgent(self, qmf_agent):
        log.debug("New agent %s", qmf_agent)

        agent_id = make_agent_id(qmf_agent)

        self.session.lock.acquire()
        try:
            self.session.qmf_agents[agent_id] = qmf_agent
        finally:
            self.session.lock.release()

    def delAgent(self, qmf_agent):
        log.debug("Deleting agent %s", qmf_agent)

        agent_id = make_agent_id(qmf_agent)

        self.session.lock.acquire()
        try:
            del self.session.qmf_agents[agent_id]
        finally:
            self.session.lock.release()

    def methodResponse(self, broker, seq, response):
        log.debug("Method response for request %i received from %s",
                 seq, broker)
        log.debug("Response: %s", response)

        self.session.lock.acquire()
        try:
            callback = self.session.outstanding_method_calls.pop(seq)
            callback(response.text, response.outArgs)
        finally:
            self.session.lock.release()
