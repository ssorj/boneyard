from update import *
from util import *

from qmf.console import Console, Session
from sage.util import get_sasl_mechanisms

log = logging.getLogger("mint.session")

class MintSession(object):
    def __init__(self, app, broker_uris):
        self.app = app
        self.broker_uris = broker_uris

        self.qmf_session = None
        self.qmf_brokers = list()

    def add_broker(self, uri):
        mechs = get_sasl_mechanisms(uri, self.app.sasl_mech_list)
        uri_without_password = uri[uri.rfind("@") + 1:]
        log.info("Adding QMF broker at %s with mech_list %s", uri_without_password, mechs)

        assert self.qmf_session

        qmf_broker = self.qmf_session.addBroker(uri, mechanisms=mechs)
        self.qmf_brokers.append(qmf_broker)

    def check(self):
        log.info("Checking %s", self)

    def init(self):
        log.info("Initializing %s", self)

    def init_qmf_classes(self):
        # Apply the package filter to the class list
        if len(self.app.qmf_classes):
            black_list = set()
            for cls in self.app.qmf_classes:
                if cls._package._name in self.app.qmf_package_filter:
                    black_list.add(cls)
            self.app.qmf_classes.difference_update(black_list)
        else:
            # Generate the package list from the model, minus
            # the package filter
            for pkg in self.app.model._packages:
                if pkg._name not in self.app.qmf_package_filter:
                    self.app.qmf_packages.add(pkg)

    def start(self):
        log.info("Starting %s", self)

        assert self.qmf_session is None

        self.qmf_session = Session(MintConsole(self.app.model),
                                   manageConnections=True,
                                   rcvObjects=True,
                                   rcvEvents=False,
                                   rcvHeartbeats=False,
                                   userBindings=True)

        if len(self.app.qmf_agents):
            for agent in self.app.qmf_agents:
                if len(agent) == 1:
                    self.qmf_session.bindAgent(label=agent[0])
                    log.info("Binding agent, label is %s" % agent[0])
                else:
                    self.qmf_session.bindAgent(vendor=agent[0], 
                                               product=agent[1], 
                                               instance=agent[2])
                    log.info("Binding agent %s:%s:%s" % (agent[0],agent[1],agent[2])) 
                    
        else:
            self.qmf_session.bindAgent("*")
            log.info("Binding all agents")
   
        # Handle bind by class
        if len(self.app.qmf_classes):
            for cls in self.app.qmf_classes:
                pname = cls._package._name
                cname = cls._name
                self.qmf_session.bindClass(pname.lower(), cname.lower())
                log.info("Binding QMF class %s.%s" % (pname, cname))
        else:            
            # Handle bind by package
            for pkg in self.app.qmf_packages:
                self.qmf_session.bindPackage(pkg._name.lower())
                log.info("Binding QMF package %s" % pkg._name)

        for uri in self.broker_uris:
            self.add_broker(uri)

    def stop(self):
        log.info("Stopping %s", self)

        for qmf_broker in self.qmf_brokers:
            self.qmf_session.delBroker(qmf_broker)

    def __repr__(self):
        uris_without_password = [x[x.rfind("@")+1:]  for x in self.broker_uris]
        return "%s(%s)" % (self.__class__.__name__, uris_without_password)

class MintConsole(Console):
    def __init__(self, model):
        self.model = model

    def brokerConnected(self, qmf_broker):
        message = "Broker %s:%i is connected"
        self.model.print_event(1, message, qmf_broker.host, qmf_broker.port)

    def brokerInfo(self, qmf_broker):
        message = "Broker info from %s:%i"
        self.model.print_event(1, message, qmf_broker.host, qmf_broker.port)

    def brokerDisconnected(self, qmf_broker):
        message = "Broker %s:%i is disconnected"
        self.model.print_event(1, message, qmf_broker.host, qmf_broker.port)

    def newAgent(self, qmf_agent):
        self.model.print_event(3, "Creating %s", qmf_agent)

        up = AgentUpdate(self.model, qmf_agent)
        self.model.app.update_thread.enqueue(up)

    def delAgent(self, qmf_agent):
        self.model.print_event(3, "Deleting %s", qmf_agent)

        up = AgentDelete(self.model, qmf_agent)
        self.model.app.update_thread.enqueue(up)

    def heartbeat(self, qmf_agent, timestamp):
        message = "Heartbeat from %s at %s"
        self.model.print_event(5, message, qmf_agent, timestamp)

        up = AgentUpdate(self.model, qmf_agent)
        self.model.app.update_thread.enqueue(up)

    def newPackage(self, name):
        self.model.print_event(2, "New package %s", name)

    def newClass(self, kind, classKey):
        self.model.print_event(2, "New class %s", classKey)

    def objectProps(self, broker, qmf_object):
        up = ObjectUpdate(self.model, qmf_object)
        self.model.app.update_thread.enqueue(up)

    def objectStats(self, broker, qmf_object):
        up = ObjectUpdate(self.model, qmf_object)
        self.model.app.update_thread.enqueue(up)

    def event(self, broker, event):
        self.model.print_event(4, "New event %s from %s", broker, event)

    def methodResponse(self, broker, seq, response):
        message = "Method response for request %i received from %s"
        self.model.print_event(3, message, seq, broker)

        log.debug("Response: %s", response)

        self.model.lock.acquire()
        try:
            callback = self.model.outstanding_method_calls.pop(seq)
            callback(response.text, response.outArgs)
        finally:
            self.model.lock.release()
