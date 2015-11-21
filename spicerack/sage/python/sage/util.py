from time import time, sleep
from threading import Thread, Lock
import re
import copy
import string

class MethodResult(object):
    '''
    Base type for synchronous method call results.
    All synchronous methods that implement remote operations
    in 'sage' will return a result whose type is this class
    or a descendent of this class.
    self.data will contain any data returned from the call
    self.got_data will be True if the call succeeded
    self.error will be True if the call raised an error
    self.status will be 'OK' or 0 if the call succeeded and
      may contain explanatory text otherwise
    '''
    def __init__(self):
        self.data = None
        self.got_data = False
        self.error = False
        self.status = None

class CallSync(MethodResult):
    '''
    General callback object for asynchronous operations.
    The 'get_completion' method will return a function that can be
    used as a callback when an asynchronous operation completes.
    To change the signature or function of the callback, derive from
    this class and override 'get_completion', changing the definition
    of the 'completion'.
    The 'done' method can be polled to determine if the operation has completed.
    '''
    def __init__(self, log=None, default=None, name=""):
        super(CallSync, self).__init__()
        self.data = default
        self.log = log
        self.meth = name

    def get_completion(self):
        # Note that because of the way binding is done in Python,
        # 'self' inside 'completion' is bound to 'obj' when 
        # obj.get_completion is called and 'completion' is returned.
        # This allows the code invoking the callback to call a simple
        # function without an object reference (the reference is hidden
        # inside the bound function).  Formally known as a "closure"

        def log_debug(self, status, data):
            if self.log:
                self.log.debug("CallSync: method '%s' returned "\
                 "status '%s' and data '%s'" % (self.meth, status, data))

        def completion(*args):
            # Callback argument formats come in two basic flavors in Cumin
            # depending on the semantics of the async op:
            # callback(status, result)
            # callback(result) where type(result) == Exception indicates
            #   a failure status
            # Allow this general mechanism to handle both types.
            data = None
            if len(args) == 0:
                # Just call it successful with no data
                status = 0
            elif len(args) == 1:
                status = args[0]
                if not isinstance(status, Exception):
                    data = status
                    status = 0
            else:
                status, data = args[0:2]

            self.status = status
            if (status == 0) or (status == "OK"):
                self.data = data
                self.got_data = True
            else:
                self.error = Exception(status)
                log_debug(self, status, data)
        return completion

    def done(self):
        return self.got_data or self.error

class SyncSet(object):
    '''
    Allows a caller to wait for completion of a set of asynchronous operations.
    A collection of CallSync objects can be built up with calls to 'add_sync'.
    'do_wait' will return when all CallSync objects in the set have been completed
    or 'timeout' seconds have elapsed.
    '''
    def __init__(self, log=None, timeout=5):
        self.syncs = dict()
        self.timeout = timeout
        self.log = log

    def add_sync(self, key, default=None, name=""):
        sync = CallSync(self.log, default, name)
        self.syncs[key] = sync
        return sync

    def do_wait(self):
        def predicate(syncs):
            done = 0
            for k, sync in syncs.items():
                if sync.done():
                    done += 1
            return done == len(syncs)

        # Wait for all syncs in the set to complete.
        # syncs will contain results for each call passed back
        # through the completion callback
        wait(predicate, timeout=self.timeout, args=self.syncs)
        return self.syncs

def wait(predicate, timeout=30, args=None):
    '''
    Simple wait routine that tests predicate() with timeout.
    If args is not None, calls predicate(args).
    '''
    start = time()
    while True:
        if args is not None:
            if predicate(args):
                return True
        else:
            if predicate():
                return True
        if time() - start > timeout:
            return False
        sleep(1)

class CallThread(Thread):
    '''
    Simple thread that executes result = routine(args).
    This thread is useful for calling synchronous routines asynchronously.
    Result is returned by calling callback(result) if callback is not None.
    If routine raises an exception, callback(exception) is called.
    '''
    def __init__(self, routine, callback, *args, **kwargs):
        super(CallThread, self).__init__()

        self.routine = routine
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.routine(*self.args, **self.kwargs)
        except Exception, e:
            result = e
        if self.callback is not None:
            self.callback(result)

def call_async(callback, call, *args, **kwargs):
    '''
    Use CallThread to execute call(*args, **kwargs).

    If callback is not None, the thread will call
    callback(result) after call() completes.
    '''
    assert callable(call)
    assert callback is None or callable(callback)

    t = CallThread(call, callback, *args, **kwargs)
    t.start()

class ObjectPool(object):
    '''
    Simple threadsafe pool class that holds up to max_size objects.
    If the pool is empty when get_object() is called an object will be
    created and returned; otherwise an object will be removed from
    the pool and returned.
    Objects are returned to the pool by a call to return_object().  If the pool
    contains less than max_size items, a reference to the object will be
    added to the pool.
    ObjectPool must be derived from, and create_object must be overridden.
    If max_size is set to None, the pool size is unlimited.
    '''
    def __init__(self, max_size):
        self.max_size = max_size
        self.pool = list()
        self.lock = Lock()

    def get_object(self):
        self.lock.acquire()
        if len(self.pool) == 0:
            self.lock.release()
            obj = self.create_object()
        else:
            obj = self.pool.pop()
            self.lock.release()
        return obj

    def return_object(self, obj):
        self.lock.acquire()
        if self.max_size is None or len(self.pool) < self.max_size:
            self.pool.append(obj)
        self.lock.release()

    def create_object(self):
        '''
        This routine must be overridden in a derived class
        to create appropriate objects for addition to the pool.
        '''
        raise Exception("Not implemented")

class sage_URL(object):
    def __init__(self, scheme, user, password, host, port, path):
        self.scheme = scheme
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.path = path

    def __repr__(self):
        return "sage_URL(%r)" % str(self)

    def __str__(self):
        s = ""
        if self.scheme:
            s += "%s://" % self.scheme
        if self.user:
            s += self.user
            if self.password:
                s += "/%s" % self.password
            s += "@"
        s += self.host
        if self.port:
            s += ":%s" % self.port
        if self.path:
            s += "/%s" % self.path 
        return s

def parse_URL(hoststring):

  RE = re.compile(r"""
        # [   <scheme>://  ] [    <user>   [   / <password>   ] @]   <host>   [   :<port>   ] [ <path> ]
        ^ (?: ([^:/@]+)://)? (?: ([^:/@]+) (?: / ([^:/@]+)   )? @)? ([^@:/]+) (?: :([0-9]+))? (?: / (.*))?$
        """, re.X)

  match = scheme = user = password = host = port = path = None
  if hoststring is not None:
      match = RE.match(hoststring)
  if match is not None:
      scheme, user, password, host, port, path = match.groups()
  return sage_URL(scheme, user, password, host, port, path)

def host_list(netlocs, default_scheme=None, default_port=None, default_path=None):
    tokens = string.split(netlocs, ",")

    hosts = dict()
    last_url = None
    last_port_set = False

    for loc in tokens:
        url = None
        loc = string.strip(loc)
        if loc.isdigit():
            # Allow just a port number to be specified if the previous
            # url explicitly set a port.  Shorthand for port list.
            # Copy all information from the previous token except port.
            if last_url is not None and last_port_set:
                url = copy.copy(last_url)
                url.port = loc
        else:
            url = parse_URL(loc)
            if url.scheme is None:
                url.scheme = default_scheme
            if url.path is None:
                url.path = default_path
            if url.port is None:
                url.port = str(default_port)
                last_port_set = False
            else:
                last_port_set = True
        last_url = url
        if url is not None and url.host is not None and url.port is not None:
            if url.host not in hosts:
                hosts[url.host] = list()
            hosts[url.host].append(url)
                
    return hosts

def get_sasl_mechanisms(uri, sasl_mech_list):
    '''
    Returns the allowable SASL mech list value.
    If sasl_mech_list is not None, it will determine the return value.
    If it is None, a default value will be chosen based on the URI.
    If sasl_mech_list is set to "AVAILABLE" then this routine will
    return None indicating the mech_list should be unrestricted.
    '''
    if sasl_mech_list is not None:
        # Leaving sasl_mech_list value unset means 'all available mechs'
        # We still need a way to say that from the config file, since
        # we have layered Cumin defaults on 'not set'
        if sasl_mech_list.upper() == "AVAILABLE":
            return None
        return sasl_mech_list

    u = parse_URL(uri)
    if u.user is not None and u.password is not None:
        mechs = "PLAIN DIGEST-MD5"
    else:
        mechs = "ANONYMOUS"
    return mechs
