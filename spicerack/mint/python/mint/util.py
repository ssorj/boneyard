import logging
import os
import random
import sys
import time

from Queue import Queue as ConcurrentQueue, Full, Empty
from crypt import crypt
from datetime import datetime, timedelta
from pprint import pprint
from getpass import getpass
from qmf.console import ObjectId
from random import sample
from tempfile import mkstemp
from threading import Thread, Lock, RLock, Condition
from time import clock, sleep
from traceback import print_exc

from parsley.collectionsex import *
from parsley.config import *
from parsley.loggingex import *
from parsley.threadingex import print_threads

log = logging.getLogger("mint.util")

class MintDaemonThread(Thread):
    def __init__(self, app):
        super(MintDaemonThread, self).__init__()

        self.app = app
        self.name = self.__class__.__name__
        self.stop_requested = False

        self.setDaemon(True)
 
    def init(self):
        pass

    def stop(self, timeout=5):
        if self.stop_requested:
            return
        self.stop_requested = True
        if self.isAlive():
            self.join(timeout)
            log.info("%s stopped" % self.getName())

class MintBlockingDaemonThread(MintDaemonThread):
    def __init__(self, app):
        super(MintBlockingDaemonThread, self).__init__(app)

        self._lock = Lock()
        self._condition = Condition(self._lock)

    def stop(self, timeout=5):
        try:
            self._condition.acquire()
            self.stop_requested = True
            self._condition.notify()
        finally:
            self._condition.release()

        if self.isAlive():
            self.join(timeout)
            log.info("%s stopped" % self.getName())

class MintPeriodicProcessThread(MintBlockingDaemonThread):
    def __init__(self, app, interval):
        super(MintPeriodicProcessThread, self).__init__(app)
        
        self.interval = interval

    def run(self):
        while True:
            start = time.time()
            try:
                self.process()
            except:
                log.info("Periodic process failed.")
                log.debug("Periodic process failed", exc_info=True)

            elapsed = time.time() - start
            delta = self.interval - elapsed

            if delta < 0:
                delta = elapsed % self.interval

            then = datetime.now() + timedelta(seconds=delta)
            try:
                self._condition.acquire()
                if not self.stop_requested:
                    log.debug("Periodic process %s sleeping until %s" \
                              % (self.getName(), then.strftime("%H:%M:%S")))
                    self._condition.wait(delta)
                if self.stop_requested:
                    log.debug("Periodic process %s exiting" % self.getName())
                    break
            finally:
                self._condition.release()

    def process(self):
        pass

def prompt_password():
    password = None

    while password is None:
        once = getpass("Enter new password: ")
        twice = getpass("Confirm new password: ")

        if once == twice:
            password = once
        else:
            print "Passwords don't match; try again"

    return password

def make_agent_id(agent):
    broker = agent.getBroker()

    if not agent.isV2 or agent is broker.getBrokerAgent():
        return "!!%s:%i!!%s" % (broker.host, broker.port, agent.getAgentBank())

    return agent.agentBank

class QmfAgentId(object):
    def __init__(self, brokerId, brokerBank, agentBank):
        assert brokerId

        self.brokerId = brokerId
        self.brokerBank = brokerBank
        self.agentBank = agentBank

    def fromObject(cls, object):
        broker = object.getBroker()

        brokerId = broker.getBrokerId()
        brokerBank = broker.getBrokerBank()
        agentBank = object.getObjectId().getAgentBank()

        return cls(brokerId, brokerBank, agentBank)

    def fromAgent(cls, agent):
        return agent.getAgentBank()

        broker = agent.getBroker()

        brokerId = broker.getBrokerId()
        brokerBank = broker.getBrokerBank()
        agentBank = agent.getAgentBank()

        print "XXX", brokerId, brokerBank, agentBank

        return cls(brokerId, brokerBank, agentBank)

    def fromString(cls, string):
        brokerId, brokerBank, agentBank = string.split(".")

        brokerBank = int(brokerBank)
        agentBank = int(agentBank)

        return cls(brokerId, brokerBank, agentBank)

    fromObject = classmethod(fromObject)
    fromAgent = classmethod(fromAgent)
    fromString = classmethod(fromString)

    def __str__(self):
        return self.agentBank

class QmfObjectId(object):
    def __init__(self, id):
        self.id = id

    def fromObject(cls, object):
        oid = object.getObjectId()

        print "XXX", oid

        for k, v in oid.__dict__.items():
            print "  ", k, v

        return cls(oid.first, oid.second)

    def fromString(cls, string):
        first, second = string.split(".")

        first = int(first)
        second = int(second)

        return cls(first, second)

    fromObject = classmethod(fromObject)
    fromString = classmethod(fromString)

    def toObjectId(self):
        return ObjectId(None, self.first, self.second)

    def __str__(self):
        return "%i.%i" % (self.first, self.second)

class UpdateQueue(ConcurrentQueue):
    def __init__(self, maxsize=0, slotCount=1):
        self.slotCount = slotCount
        ConcurrentQueue.__init__(self, maxsize)

    def _init(self, maxsize):
        self.maxsize = maxsize
        self.slots = []

        for i in range(self.slotCount):
            self.slots.append(deque())

    def _qsize(self):
        size = 0

        for i in range(self.slotCount):
            size += len(self.slots[i])

        return size

    def _empty(self):
        return self._qsize() == 0

    def _full(self):
        return self.maxsize > 0 and self._qsize() == self.maxsize

    def _put(self, update):
        slot = update.priority

        if slot in range(self.slotCount):
            self.slots[slot].append(update)
        else:
            raise ValueError("Invalid priority slot")

    def _get(self):
        for slot in range(self.slotCount):
            if len(self.slots[slot]) > 0:
                return self.slots[slot].popleft()

        return None

password_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def crypt_password(password, salt=None):
    if not salt:
        salt = "".join(sample(password_chars, 2))

    return crypt(password, salt)

def ess(num, ending="s"):
    return num != 1 and ending or ""

class ProfilerThread(object):
    def calibrate(self, prof):
        print "Calibrating"
        
        biases = list()
    
        for i in range(3):
            bias = prof.calibrate(50000)
            biases.append(bias)
            print i, bias
        
        prof.bias = sum(biases) / float(3)

        print "Using bias %f" % prof.bias

    def run(self):
        from cProfile import Profile
        from pstats import Stats

        prof = Profile()

        if hasattr(prof, "calibrate"):
            self.calibrate(prof)

        prof.runctx("self.do_run()",
                    globals=globals(),
                    locals=locals())

        fd, path = mkstemp(".profile")

        prof.dump_stats(path)

        stats = Stats(path)

        stats.sort_stats("cumulative").print_stats(15)
        stats.sort_stats("time").print_stats(15)

    def do_run(self):
        raise Exception("Not implemented")
