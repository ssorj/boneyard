import logging
from sage.util import CallSync, wait

log = logging.getLogger("sage.qmf")

class QmfOperations(object):
    '''
    Provides an interface to QMF remote procedure calls.
    Public methods may implement synchronous or asynchronous
    calling semantics, or may support either one depending on the parameters
    passed.
    If a method takes a 'callback' parameter and that parameter is not
    None, the method will have asynchronous calling semantics.  Otherwise,
    the method will have synchronous calling semantics and the 'default' and
    'timeout' parameters will be used.
    The type of the result returned from all synchronous methods will be
    sage.util.MethodResult or a descendent.
    The 'callback' parameter if set is expected to be a reference to a
    function that can be invoked by self.session.call_method() when an 
    operation is complete.
    '''

    def __init__(self, name, session):
        '''
        If this object is added to a Catalog object as a mechanism,
        the 'name' parameter will be used to create an attribute which points
        to this object.
        The 'session' parameter is expected to be an object that defines the
        following method:

            def call_method(callback, obj, meth, args)

        session.call_method should be capable of invoking the 'meth' method
        on the 'obj' object with the tuple 'args' as arguments.  It should
        be capable of passing results to the 'callback' function.  Any 
        'callback' parameter passed to a public method of a QmfOperations object
        should have a signature that is compatible with that expected by 
        session.call_method().
        '''

        self.name = name
        self.session = session

    # Note, methods below were written to be synchronous, asynchronous, or 
    # selectable to reflect existing usage of QMF methods in cumin at 
    # the time 'sage' was created.  Any of these methods may be changed to
    # have synchronous or asynchronous calling semantics by using the callback,
    # default, and timeout paramters and the self._call method.

# broker operations

    def queue_move_messages(self, broker, src, dst, count, callback):
        assert callback
        self._call(broker, "queueMoveMessages", callback, 0, 0, src, dst, count)

# methods on various broker objects.  close is implemented on multiple objects

    def close(self, obj, callback):
        assert callback
        self._call(obj, "close", callback, 0, 0)

    def detach(self, obj, callback):
        assert callback
        self._call(obj, "detach", callback, 0, 0)

    def bridge(self, link, durable, src, dest, key, tag, excludes, srcIsQueue, srcIsLocal, dynamic, sync, callback):
        assert callback
        self._call(link, "bridge", callback, 0, 0,
                   durable, src, dest, key, tag, excludes, srcIsQueue, srcIsLocal, dynamic, sync)

    def connect(self, obj, host, port, durable, mech, username, password, transport, callback):
        assert callback
        self._call(obj, "connect", callback, 0, 0,
                    host, port, durable, mech, username, password, transport)      

# queue operations

    def purge_queue(self, queue, count, callback):
        assert callback
        self._call(queue, "purge", callback, 0, 0, count)

# scheduler operations

    def set_job_attribute(self, scheduler, job_id, name, value, callback, *args):
        assert callback
        self._call(scheduler, "SetJobAttribute", callback, 0, 0,
                   job_id, name, value)

    def submit_job(self, scheduler, ad, callback):
        assert callback
        self._call(scheduler, "SubmitJob", callback, 0, 0, ad)

    def control_job(self, cmd, scheduler, job_id, reason, *args, **kwargs):
        '''
        This method is asynchronous iff 'callback' is supplied.

        Values for cmd are case sensitive (although the first letter may
        actually be either case) and may be one of the following:
            'HoldJob', 'ReleaseJob', 'SuspendJob', 'ContinueJob', 'RemoveJob'
        
        kwargs will be searched for 'callback', 'default' and 'timeout' arguments.
        '''

        # Aviary and QMF command names for job control differ in one respect,
        # which is that QMF uses an initial capital and Aviary does not.
        # Make sure initial letter is uppercase
        cmd = cmd[0].upper() + cmd[1:]

        callback = "callback" in kwargs and kwargs["callback"] or None
        default = "default" in kwargs and kwargs["default"] or None
        timeout = "timeout" in kwargs and kwargs["timeout"] or 5

        return self._call(scheduler, cmd, callback, default,
                          timeout, job_id, reason)

# jobserver operations 

    def get_job_ad(self, job_server, job_id, *args, **kwargs):
        '''
        kwargs will be searched for 'default' and 'timeout' arguments.

        These optional arguments were moved to kwargs for compatibility
        with another implementation of the same routine.
        '''

        default = "default" in kwargs and kwargs["default"] or None
        timeout = "timeout" in kwargs and kwargs["timeout"] or 5

        return self._call(job_server, "GetJobAd", 0, default, timeout, job_id)

    def fetch_job_data(self, job_server, job_id, ftype, file, start, end,
                       *args, **kwargs):
        '''
        kwargs will be searched for 'default' and 'timeout' arguments.

        These optional arguments were moved to kwargs for compatibility
        with another implementation of the same routine.
        '''

        default = "default" in kwargs and kwargs["default"] or None
        timeout = "timeout" in kwargs and kwargs["timeout"] or 5
            
        # QMF doesn't use the ftype value, it just uses the filename
        return self._call(job_server, "FetchJobData", 0, default, timeout,
                          job_id, file, start, end)

# negotiator operations

    def set_limit(self, negotiator, lim_name, lim_max, *args, **kwargs):
        '''
        This method is asynchronous iff 'callback' is supplied.

        kwargs will be searched for 'callback', 'default' and 'timeout' arguments.
        '''

        callback = "callback" in kwargs and kwargs["callback"] or None
        default = "default" in kwargs and kwargs["default"] or None
        timeout = "timeout" in kwargs and kwargs["timeout"] or 5

        return self._call(negotiator, "SetLimit", callback, default, 
                          timeout, lim_name, lim_max)

    def get_limits(self, negotiator, callback):
        assert callback
        return self._call(negotiator, "GetLimits", callback, 0, 0) 

    def reconfig(self, negotiator, *args, **kwargs):
        '''
        This method is asynchronous iff 'callback' is supplied.

        kwargs will be searched for 'callback', 'default' and 'timeout' arguments.
        '''

        callback = "callback" in kwargs and kwargs["callback"] or None
        default = "default" in kwargs and kwargs["default"] or None
        timeout = "timeout" in kwargs and kwargs["timeout"] or 5

        return self._call(negotiator, "Reconfig", callback, default, timeout)

    def set_raw_config(self, negotiator, name, value, default=None, timeout=5):
        return self._call(negotiator, "SetRawConfig", 0, default, timeout,
                          name, value)

    def get_raw_config(self, negotiator, name, callback):
        assert callback
        return self._call(negotiator, "GetRawConfig", callback, 0, 0, name)

# master operations

    def start(self, master, daemon, callback):
        assert callback
        return self._call(master, "Start", callback, 0, 0, daemon)

    def stop(self, master, daemon, callback):
        assert callback
        return self._call(master, "Stop", callback, 0, 0, daemon)

# submission operations

    def get_job_summaries(self, submission, callback, *args):
        assert callback
        return self._call(submission, "GetJobSummaries", callback, 0, 0)

# Secret private implementation stuff, don't look!
    def _call(self, obj, meth, cb, dflt, tout, *args):

        if cb:
            self.session.call_method(cb, obj, meth, args)
        else:
            try:
                sync = CallSync(log, dflt, meth)
                self.session.call_method(sync.get_completion(),
                                         obj, meth, args)
            except Exception, e:
                sync.error = e
                log.debug("QMF method call exception", exc_info=True)

            wait(sync.done, timeout=tout)
            if not sync.got_data and not sync.error:
                sync.error = Exception("Request timed out")
                msg = "QMF call %s timed out" % meth
                log.error(msg)
            return sync

