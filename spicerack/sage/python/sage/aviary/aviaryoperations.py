import os
import threading
import logging
import random
import urllib2
import string
import time
import sage
import socket

from datetime import datetime
from threading import Lock
from suds import *
from sage.util import CallSync, CallThread, ObjectPool, host_list
from aviarylocator import AviaryLocator
from clients import ClientPool, TransportFactory

log = logging.getLogger("sage.aviary")

class SudsLogging(object):
    _on = False
    sudslogs = {"suds.client": None, "suds.transport": None, "suds.xsd.schema": None, "suds.wsdl": None}

    @classmethod
    def set(cls, flag, home):
        if flag:
            SudsLogging._on = True
            for k,v in SudsLogging.sudslogs.iteritems():
                l = logging.getLogger(k)
                l.setLevel(logging.DEBUG)
                try:
                    f = open(os.path.join(home, "log/"+k+".log"), 'a+')
                    h = logging.StreamHandler(f)
                    l.addHandler(h)
                    SudsLogging.sudslogs[k] = h
                except:
                    pass
            log.debug("AviaryOperations: suds logging on")

        elif SudsLogging._on:
            SudsLogging._on = False
            for k,v in SudsLogging.sudslogs.iteritems():
                try:
                    logging.getLogger(k).removeHandler(v)
                except:
                    pass
            log.debug("AviaryOperations: suds logging off")


#Stuff to do:

#- Test pool/schedd/stuff with hierarchical collectors

#- Add a summary comment at the top like QMF opreations

#- can we use default/timeout with suds?
#looks like the way to do this is through the Transport object that
#is set in the client.  The timeout is set on the Transport itself,
#and the Transport can be changed on the client with set_options.
#Alternatively, we could retain a reference to the Transport in 
#the clients that we pool so that we can call set_options on the
#transport.

def _get_host(name, servers):
    '''
    Lookup a host in a dictionary produced by sage.util.host_list.
    Return the scheme and URL for the host.
    '''
    scheme = ""
    host = ""
    if name in servers:
        urls = servers[name]
        if len(urls) > 0:
            url = random.sample(urls, 1)[0]
            scheme = url.scheme
            host = str(url)
            # A particular method name is going to be appended to path,
            # so ensure the final "/" here.
            if not host.endswith("/"):
                host += "/"
    return scheme, host

# Nice, friendly strings for error messages on lookup
_nice = {"JOB": "job service",
         "QUERY_SERVER": "query service"}

class ServerList(object):
    '''
    Query an Aviary locator object for endpoints by reource and subtype.
    Lookup an endpoint of the specified type by machine name.
    Allow the cached list to be refreshed on demand.
    '''
    def __init__(self, locator, resource, subtype):

        # Since we have a dynamic server list, failed operations
        # may be retried
        self.should_retry = True

        self._lock = Lock()
        self.servers = None
        self.locator = locator
        self.resource = resource
        self.subtype = subtype

        try:
            self.nice = _nice[subtype]
        except:
            self.nice = subtype

    def _find_server(self, machine, refresh=False):
        '''
        Search the cached server list for machine using _get_host.
        If the server list is empty or refresh is True, get a new list
        of endpoints from the Aviary locator object and generate a new
        server list.
        '''
        # If we already have a list of values then return that list unless
        # refresh is True
        self._lock.acquire()
        try:
            if self.servers is None or refresh:
                log.debug("AviaryOperations: refresh server list for %s %s" \
                              % (self.resource, self.subtype))
                try:
                    result = self.locator.get_endpoints(self.resource, 
                                                        self.subtype)
                except Exception, e:
                    result = _AviaryCommon._pretty_result(e, 
                                                     self.locator.locator_uri)
                    log.debug("AviaryOperations: failed to get endpoints, " \
                              "exception message '%s'" % result.message)
                    raise result

                urls = []
                # If it's not okay, we just produce an empty sever list
                if result.status.code == "OK":
                    for r in result.resources:
                        urls.extend(r.location)
                urls = ",".join(urls)
                if urls == "":
                    log.info("AviaryOperations: locator returned " \
                             "no endpoints for %s %s" % (self.resource,
                                                         self.subtype))

                # Parse the urls and produce a dictionary of
                # sage_URLs by machine
                self.servers = host_list(urls)

            scheme, host = _get_host(machine, self.servers)
        finally:
            self._lock.release()
        return scheme, host

    def find_server(self, machine, refresh=False):
        '''
        Lookup a URL in the cached server list by machine.
        Generate a new server list if refresh is True, or if the
        initial host lookup fails and refresh == "on_no_host".
        Return the scheme and URL for the specified machine.
        '''
        # Update the list if necessary and return host info for machine.
        # If refresh is True, the server list will be updated.  This is
        # used when a previously cached host fails during a remote method
        # invocation and we want to do a retry before giving up.
        scheme, host = self._find_server(machine, refresh is True)
        if host == "" and refresh == "on_no_host":
            # Okay, if we didn't find a host and on_no_host has been set,
            # try one more time with a forced refresh before we error.
            # The case here is that the service on the particular host has
            # not yet been discovered since Cumin startup or the last refresh.
            # But, the service may appear at any point so it's possible that
            # it's there now.  Think "on demand polling".
            scheme, host = self._find_server(machine, True)
        if host == "":
            log.info("AviaryOperations: failed to locate %s on %s" \
                         % (self.nice, machine))
            raise Exception("Cannot locate %s on %s via aviary locator" \
                                % (self.nice, machine))
        return scheme, host

class FixedServerList(object):
    '''
    Allows lookup for endpoints by machine when the server list is fixed.
    '''
    def __init__(self, servers, port, path, subtype):
        # Fixed server list, there is no point to a retry on failed ops.
        self.should_retry = False
        
        # Replace any occurrence of locahost with output of gethostname()
        # before parsing to match Machine fields of QMF objects later on.
        host = socket.gethostname()
        servers = string.replace(servers, "localhost", host)

        self.servers = host_list(servers, 
                                 default_scheme="http", 
                                 default_port=port,
                                 default_path=path)

        try:
            self.nice = _nice[subtype]
        except:
            self.nice = subtype

    def find_server(self, machine, *args):
        scheme, host = _get_host(machine, self.servers)
        if host == "":
            log.info("AviaryOperations: failed to locate %s on %s" \
                         % (self.nice, machine))
            raise Exception("Cannot locate %s on %s, check aviary " \
                            "settings in cumin.conf" % (self.nice, machine))
        return scheme, host

class _AviaryJobMethods(object):

    # Do this here rather than __init__ so we don't have to worry about
    # matching parameter lists in multiple inheritance cases with super
    def init(self, datadir, job_servers):

        if self.locator:
            self.job_servers = ServerList(self.locator, "SCHEDULER", "JOB")
        else:
            self.job_servers = FixedServerList(job_servers, 
                                               "9090", 
                                               "/services/job/",
                                               "JOB")

        

        job_wsdl = "file:" + os.path.join(self.get_datadir(datadir,"job"),
                                          "aviary-job.wsdl")
        self.job_client_pool = ClientPool(job_wsdl, None)

    def set_job_attribute(self, scheduler, job_id, name, value, callback, submission):
        assert callback
        
        def my_callback(result):
            self.job_client_pool.return_object(job_client)
            result = self._pretty_result(result, scheduler.Machine)
            # massage results for use by standard callback
            cb_args = self._cb_args_dataless(result)
            callback(*cb_args)

        job_client = self.job_client_pool.get_object()
        self._setup_client(job_client, 
                           self.job_servers,   # server lookup object
                           scheduler.Machine,  # host we want
                           "setJobAttribute")
                                   
        # Make a job id parameter (see job wsdl)
        jobId = job_client.factory.create('ns0:JobID')
        jobId.job = job_id
        jobId.pool = scheduler.Pool
        jobId.scheduler = scheduler.Name
        jobId.submission.name = submission.Name
        jobId.submission.owner = submission.Owner

        # Make attribute parameter from name and value
        aviary_attr = job_client.factory.create('ns0:Attribute')
        aviary_attr.name = name
        aviary_attr.type = "STRING"
        aviary_attr.value = value

        t = CallThread(self.call_client_retry, my_callback, 
                       job_client, "setJobAttribute", jobId, aviary_attr)
        t.start()

    def submit_job(self, scheduler, ad, callback):
        assert callback

        def my_callback(result):
            # Turn this back off before we put it back in the pool
            # so allow_overrides isn't set for someone else...
            job_client.set_enable_attributes(False)
            self.job_client_pool.return_object(job_client)
            result = self._pretty_result(result, scheduler.Machine)
            if isinstance(result, Exception):
                callback(result, None)                
            else:
                # the aviary response has the job id available,
                # we'll pass it anyway even though Cumin does not care
                # at the present time
                status = _AviaryCommon._get_status(result.status)
                if status == "OK" and hasattr(result, "id"):
                    id = result.id
                else:
                    id = None
                callback(status, id)

        job_client = self.job_client_pool.get_object()
        self._setup_client(job_client, 
                           self.job_servers,    # server lookup object
                           scheduler.Machine,  # host we want
                           "submitJob")

        # Set basic attributes in the order defined by aviary-job.wsdl.
        args = list()
        basic_attrs = ("Cmd", "Args", "Owner", "Iwd", "Submission")
        for attr in basic_attrs:
            try:
                args.append(ad[attr])
            except:
                # Someone may be unhappy if this is a required param!
                # Let the downstream code generate an error
                pass

        # Add empty list for Aviary's basic requirement value...
        args.append([])

        # and let's let Requirements remain an unrestricted expression so that
        # we can just pass through the value from Cumin without interfering.
        # To do that, we need to specify Requirements through the
        # "extras" fields and set allowOverrides to True.
        # (otherwise, Requirements will be limited to particular
        # resource constraint types defined by aviary)
        job_client.set_enable_attributes(True)
        job_client.set_attributes({"allowOverrides": True})
        extras = list()
        for k, v in ad.iteritems():
            # We don't need to send descriptors down to aviary
            # and basic_attrs have already been filled in
            if k == "!!descriptors" or k in basic_attrs:
                continue
            
            extra = job_client.factory.create('ns0:Attribute')
            extra.name = k
            # But we do need to look in descriptors to find expressions...
            if k in ad["!!descriptors"]:
                extra.type = "EXPRESSION"
            else:
                try:
                    extra.type = self.type_to_aviary[type(v)]
                except KeyError:
                    extra.type = "UNDEFINED"
            extra.value = v
            extras.append(extra)

        # Important, extras itself must be added as an embedded list or 
        # suds will consider only a single item
        args.append(extras)

        t = CallThread(self.call_client_retry, my_callback, 
                       job_client, "submitJob", *args)
        t.start()

    def control_job(self, cmd, scheduler, job_id, reason, submission, *args, **kwargs):
        '''
        This method is asynchronous iff 'callback' is supplied.

        Values for cmd are case sensitive (although the first letter may
        actually be either case) and may be one of the following:
            'holdJob', 'releaseJob', 'suspendJob', 'continueJob', 'removeJob'
        
        kwargs will be searched for 'callback', 'default' and 'timeout' arguments.
        '''

        # Aviary and QMF command names for job control differ in one respect,
        # which is that QMF uses an initial capital and Aviary does not.
        cmd = cmd[0].lower() + cmd[1:]
        return self._control_job(scheduler, job_id, reason, submission,
                                 cmd, *args, **kwargs)

    def _control_job(self, scheduler, job_id, reason, submission,
                     meth_name, *args, **kwargs):

        callback = "callback" in kwargs and kwargs["callback"] or None
        default = "default" in kwargs and kwargs["default"] or None
        timeout = "timeout" in kwargs and kwargs["timeout"] or 5

        client = self.job_client_pool.get_object()
        self._setup_client(client, 
                           self.job_servers,    # server lookup object
                           scheduler.Machine,  # host we want
                           meth_name)

        meth = getattr(client.service, meth_name)

        # Make a job id parameter (see job wsdl)
        jobId = client.factory.create('ns0:JobID')
        jobId.job = job_id
        jobId.pool = scheduler.Pool
        jobId.scheduler = scheduler.Name
        jobId.submission.name = submission.Name
        jobId.submission.owner = submission.Owner

        if callback:
            def my_callback(result):
                self.job_client_pool.return_object(client)
                # Fix up the exception message if necessary
                result = self._pretty_result(result, scheduler.Machine)
                cb_args = self._cb_args_dataless(result)
                callback(*cb_args)

            t = CallThread(self.call_client_retry, my_callback,
                           client, meth_name, jobId, reason)
            t.start()
        else:
            def my_process_results(result):
                # Fix up the exception message if necessary
                result = self._pretty_result(result, scheduler.Machine)
                return self._cb_args_dataless(result)

            res = self._call_sync(my_process_results, self.call_client_retry, 
                                  client, meth_name, jobId, reason) 
            self.job_client_pool.return_object(client)
            return res;

class _AviaryQueryMethods(object):

    # Do this here rather than __init__ so we don't have to worry about
    # matching parameter lists in multiple inheritance cases with super
    def init(self, datadir, query_servers):

        if self.locator:
            self.query_servers = ServerList(self.locator, 
                                            "CUSTOM", "QUERY_SERVER")
        else:
            self.query_servers = FixedServerList(query_servers, 
                                                 "9091", 
                                                 "/services/query/", 
                                                 "QUERY_SERVER")

        query_wsdl = "file:" + os.path.join(self.get_datadir(datadir,"query"), 
                                            "aviary-query.wsdl")
        self.query_client_pool = ClientPool(query_wsdl, None)

    def fetch_job_data(self, job_server, job_id, ftype, file, start, end,
                       scheduler_name, submission, *args, **kwargs):
        '''
        kwargs will be searched for 'default' and 'timeout' arguments.

        These optional arguments were moved to kwargs for compatibility
        with another implementation of the same routine.
        '''

        default = "default" in kwargs and kwargs["default"] or None
        timeout = "timeout" in kwargs and kwargs["timeout"] or 5

        # Aviary doesn't use the file name as does QMF, instead it
        # specifies the file type and lets condor figure out the path.

        def my_process_results(result):
            # Fix up the exception message if necessary
            result = self._pretty_result(result, job_server.Machine)
            if isinstance(result, Exception):
                status = result
                data = None
            else:
                status = _AviaryCommon._get_status(result.status)
                if status == "OK" and hasattr(result, "content"):
                    # Match the format expected by Cumin.  This is
                    # the format used by the QMF call...
                    data = {'Data': result.content}
                else:
                    data = None
            return (status, data)

        client = self.query_client_pool.get_object()
        self._setup_client(client, 
                           self.query_servers,  # server lookup object
                           job_server.Machine,  # host we want
                           "getJobData")

        # Make a job data parameter (see query wsdl)
        jobData = client.factory.create('ns0:JobData')
        jobData.id.job = job_id
        jobData.id.pool = job_server.Pool
        jobData.id.scheduler = scheduler_name
        jobData.id.submission.name = submission.Name
        jobData.id.submission.owner = submission.Owner

        # Translate cumin file type to Aviary file type
        if ftype == "e":
            jobData.type = "ERR"
        elif ftype == "o":
            jobData.type = "OUT"
        elif ftype == "u":
            jobData.type = "LOG"
        else:
            # We can't translate the type.
            # Let Aviary throw an error on this instead of us.
            jobData.type = ftype

        from_end = start < 0
        max_bytes = abs(end - start)

        res = self._call_sync(my_process_results, self.call_client_retry,
                              client, "getJobData", jobData, max_bytes, from_end)
        self.query_client_pool.return_object(client)
        return res;

    def get_job_ad(self, job_server, job_id, scheduler_name, submission, 
                   *args, **kwargs):
        '''
        kwargs will be searched for 'default' and 'timeout' arguments.

        These optional arguments were moved to kwargs for compatibility
        with another implementation of the same routine.
        '''        

        default = "default" in kwargs and kwargs["default"] or None
        timeout = "timeout" in kwargs and kwargs["timeout"] or 5

        def make_tuple(attr):
            # Attempt to cast the value into the specified type
            if attr.type in self.aviary_to_type:
                try:
                    v = self.aviary_to_type[attr.type](attr.value)
                except:
                    v = attr.value
            else:
                v = attr.value
            return (attr.name, v)
        
        def make_dict(attrs):
            return dict([make_tuple(attr) for attr in attrs])

        def my_process_results(result):
            # Fix up the exception message if necessary
            result = self._pretty_result(result, job_server.Machine)
            if isinstance(result, Exception):
                status = result
                data = None
            else:
                status = _AviaryCommon._get_status(result[0].status)
                if status == "OK":
                    # Match the format expected by Cumin.  This is
                    # the format used by the QMF call.  We have a list
                    # of attributes in attrs that we need to make into
                    # a dictionary
                    ads = make_dict(result[0].details.attrs) 
                    data = {'JobAd': ads}
                else:
                    data = None
            return (status, data)

        client = self.query_client_pool.get_object()
        self._setup_client(client, 
                           self.query_servers,  # server lookup object
                           job_server.Machine,  # host we want
                           "getJobDetails")

        # Make a job id parameter (see job wsdl)
        jobId = client.factory.create('ns0:JobID')
        jobId.job = job_id
        jobId.pool = job_server.Pool
        jobId.scheduler = scheduler_name
        jobId.submission.name = submission.Name
        jobId.submission.owner = submission.Owner

        res = self._call_sync(my_process_results, self.call_client_retry,
                              client, "getJobDetails", jobId)
        self.query_client_pool.return_object(client)
        return res;

    def get_job_summaries(self, submission, callback, machine_name):
        assert callback

        def to_int_seconds(dt):
            # Change a datetime.datetime into int seconds since epoch
            # Note, this works nicely if the datetime happens to include microseconds
            # since the call to timetuple will drop them.  Stuff coming back from
            # condor should not have microseconds anyway.
            return int(time.mktime(dt.timetuple()))

        def get_string(job, attr):
            # Cast suds text types into str so we have standard Py types
            # Handles optional strings as well
            if hasattr(job, attr):
                return str(getattr(job, attr))
            return ""

        def adapt(jobs):
            # Make an aviary job summary look like the canonical form
            # that cumin is expecting (actually the QMF form because of history).
            result = list()
            for job in jobs:
                cluster, proc = job.id.job.split(".")
                j = dict()
                j["ClusterId"]            = int(cluster)
                j["Cmd"]                  = str(job.cmd)
                j["EnteredCurrentStatus"] = to_int_seconds(job.last_update)

                # Note, GlobalJobId here will not match the same value from
                # QMF because the qdate portion of the name is missing
                j["GlobalJobId"]          = job.id.scheduler + \
                                            "#" + job.id.job

                j["JobStatus"]            = str(job.job_status)
                j["ProcId"]               = int(proc)
                j["QDate"]                = to_int_seconds(job.queued)
                
                # These may be null...
                j["Args"]                 = get_string(job, "args1")
                j["ReleaseReason"]        = get_string(job, "released")
                j["HoldReason"]           = get_string(job, "held")
                result.append(j)
            return result
                
        def my_callback(result):
            query_client.set_enable_attributes(False)
            self.query_client_pool.return_object(query_client)
            result = self._pretty_result(result, machine_name)
            if isinstance(result, Exception):
                callback(result, None)                
            else:
                status =  _AviaryCommon._get_status(result[0].status)
                if status == "OK" and hasattr(result[0], "jobs"):
                    data = {"Jobs": adapt(result[0].jobs)}
                else:
                    data = {"Jobs": None}
                callback(status, data)

        query_client = self.query_client_pool.get_object()
        self._setup_client(query_client, 
                           self.query_servers,  # server lookup object
                           machine_name,        # host we want
                           "getSubmissionSummary")

        # What we really want here is the job summaries from the
        # submission summary response.  To get those, we have to
        # set an extra attribute on the client...
        query_client.set_enable_attributes(True)
        query_client.set_attributes({"includeJobSummaries": "true"})

        # Make a submission id.  (see query wsdl)
        subId = query_client.factory.create('ns0:SubmissionID')
        subId.name = submission.Name
        subId.owner = submission.Owner

        t = CallThread(self.call_client_retry, my_callback, 
                       query_client, "getSubmissionSummary", subId)
        t.start()


class _AviaryCommon(object):
    def __init__(self, name, locator, 
                 key="", cert="", root_cert="", domain_verify=True):

        self.transports = TransportFactory(key, cert, root_cert, domain_verify)

        # Log init messages from TransportFactory
        self.transports.log_details(log, "AviaryOperations")
        self.name = name

        # Put this here to be referenced by AviaryOperations types
        self.locator = locator

        self.type_to_aviary = self._type_to_aviary()
        self.aviary_to_type = self._aviary_to_type()

    def get_datadir(self, datadir, subdir):
        if not type(datadir) in (tuple, list):
            datadir = [datadir]

        # Find the first element in datadir that is a valid
        # path.  If the path has a subdirectory called 
        # "subdir", consider that part of the path.
        for d in datadir:
            if os.path.isdir(d):
                s = os.path.join(d, subdir)
                if os.path.isdir(s):
                    return s
                return d
        # Hmm, well, just return the first one since we're
        # going to get an error anyway.
        return datadir[0]

    @classmethod
    def _type_to_aviary(cls):
        # Need to be able to turn simple Python types into Aviary types for attributes
        return {int: "INTEGER", float: "FLOAT", str: "STRING", bool: "BOOLEAN"}

    @classmethod
    def _aviary_to_type(cls):
        return {"INTEGER": int, "FLOAT": float, "STRING": str, "BOOLEAN": bool}

    def _set_client_info(self, client, refresh=False):
        scheme, host = client.server_list.find_server(client.service_name, 
                                                      refresh)

        # Have to set the URL for the method.  This might go away someday...
        client.set_options(location=host+client.method_name)

        # Since we pool the clients and reuse them for different requests
        # and since its possible to be using servers with different schemes,
        # we have to always reset the transport here.
        the_transport = self.transports.get_transport(scheme)
        client.set_options(transport=the_transport)

    def _setup_client(self, client, server_list, name, meth_name):
        # Look up the host and construct the URL.
        # Store information in the client so that retry is possible.
        client.server_list = server_list
        client.service_name = name
        client.method_name = meth_name

        # This is initial setup before a call so we want to try a 
        # refresh on the server list if our service comes up missing
        self._set_client_info(client, refresh="on_no_host")
        return client

    @classmethod
    def _get_status(cls, result):
        # For Aviary operations, if the operation
        # did not work the reason is in the text field.
        # In cumin, we want to pass any error text as
        # the status parameter to callbacks
        if result.code != "OK":
            return result.text
        return result.code

    @classmethod
    def _cb_args_dataless(cls, result):
        # Marshal data in result for passing to standard callback.
        # This routine is for results that contain status only, no data.
        if isinstance(result, Exception):
            status = result
        else:
            status = _AviaryCommon._get_status(result)
        return (status, None)

    @classmethod
    def _pretty_result(cls, result, host):
        if isinstance(result, urllib2.URLError):
            return Exception("Trouble reaching host %s, %s" % (host, result.reason))
        elif isinstance(result, Exception):
            if hasattr(result, "args"):
                reason = result.args
            else:
                reason = str(result)
            return Exception("Operation failed on host %s, %s" % (host, reason))
        return result

    def call_client_retry(self, client, meth_name, *meth_args, **meth_kwargs):
        # If we fail with a urllib2.URLError (or anything similar) then try
        # attempt to get a new endpoint and try again.
        meth = getattr(client.service, meth_name)
        try:
            result = meth(*meth_args, **meth_kwargs)
        except Exception, e:
            # If we get an exception, our endpoint may have moved 
            # (probably due to a restart on the condor side)
            # Let's get new endpoints, reset the client, 
            # and try again.
            if client.server_list.should_retry:
                log.debug("AviaryOperations: received %s, retrying %s"\
                              % (str(e), client.options.location))
                self._set_client_info(client, refresh=True)
                result = meth(*meth_args, **meth_kwargs)
            else:
                raise e
        return result

    def _call_sync(self, process_results, meth, *meth_args, **meth_kwargs):
        # Common interface with QMF operations requires that a MethodResult
        # object (or something just like it) be returned for synchronous calls.
        # Might as well use the CallSync since the completion() routine 
        # handles status semantics.

        # meth here is a suds.client.Method which has a name attr....
        sync = CallSync(log, name=meth.__name__)
        try:
            result = meth(*meth_args, **meth_kwargs)
        except Exception, e:
            result = e
        cb_args = process_results(result)
        sync.get_completion()(*cb_args) 
        return sync

class AviaryOperations(_AviaryCommon, _AviaryJobMethods, _AviaryQueryMethods):
    def __init__(self, name, datadir, locator, job_servers, query_servers,
                 key="", cert="", root_cert="", domain_verify=True):

        super(AviaryOperations, self).__init__(name, locator,
                                               key, cert, root_cert, 
                                               domain_verify)

        _AviaryJobMethods.init(self, datadir, job_servers)
        _AviaryQueryMethods.init(self, datadir, query_servers)


class AviaryJobOperations(_AviaryCommon, _AviaryJobMethods):
    def __init__(self, name, datadir, locator, job_servers,
                 key="", cert="", root_cert="", domain_verify=True):

        super(AviaryJobOperations, self).__init__(name, locator, 
                                                  key, cert, root_cert, 
                                                  domain_verify)
        
        _AviaryJobMethods.init(self, datadir, job_servers)

class AviaryQueryOperations(_AviaryCommon, _AviaryQueryMethods):
    def __init__(self, name, datadir, locator, query_servers,
                 key="", cert="", root_cert="", domain_verify=True):

        super(AviaryQueryOperations, self).__init__(name, locator, 
                                                    key, cert, root_cert, 
                                                    domain_verify)

        _AviaryQueryMethods.init(self, datadir, query_servers)

def AviaryOperationsFactory(name, datadir, locator_uri, 
                            job_servers, query_servers,
                            key="", cert="", root_cert="", domain_verify=True):

    # If locator uri has not been specified, it's disabled and we will
    # use the specified job_servers and query_servers values
    if locator_uri:
        locator = AviaryLocator(datadir, locator_uri,
                                key, cert, root_cert, domain_verify)
    else:
        locator = None

    if job_servers and query_servers:
        res = AviaryOperations(name, datadir, locator,
                               job_servers, query_servers,
                               key, cert, root_cert, domain_verify)
    elif job_servers:
        res = AviaryJobOperations(name, datadir, locator,job_servers,
                                  key, cert, root_cert, domain_verify)
    elif query_servers:
        res = AviaryQueryOperations(name, datadir, locator,query_servers,
                                    key, cert, root_cert, domain_verify)
    return res

