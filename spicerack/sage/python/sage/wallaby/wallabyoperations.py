import logging

import time
from qmf.console import Session
from sage.util import CallThread, get_sasl_mechanisms
from threading import Lock, Condition

#import cProfile

imports_ok = True
try:
   import wallaby
   import wallaby.tagging
   import wallaby.collections
   setup = wallaby.tagging.setup
except:
    imports_ok = False

log = logging.getLogger("sage.wallaby")

class WBTypes:
    '''
    Wrap symbolic names for data items tracked by WallabyOperations.
    May be helpful in avoiding typos, good for interpreter help
    '''
    NODES = "nodes"
    GROUPS = "groups"
    TAGS = "tags"
    FEATURES = "features"

if imports_ok:
    class WallabyOperations(object):
        '''
        Wrapper around the Wallaby client library.
        '''
        def __init__(self, broker_uri, refresh_interval=None, sasl_mech_list=None):
            '''
            Constructor.

            broker_uri -- the URI used to connect to a QMF message broker
            where a Wallaby agent is connected.  The simplest URI is just a
            hostname but a full URI can specify scheme://user/password@host:port
            or a subset of those components as long as the host is included.
            Examples:

                localhost
                localhost:5672
                amqp://fred/flintsone@quarry.bedrock.com:1234

            refresh_interval -- default refresh interval in seconds for all items
            maintained by WallabyOperations' internal caching thread.  A value of 
            None causes the caching thread to wait forever before refreshing an 
            item after a successful call unless the refresh() method is used.
            The refresh interval may be set for items individually with the
            set_interval() method.

            sasl_mech_list -- restricts the list of sasl mechanisms
            that will be allowed when connecting to a QMF message broker.
            If the broker URL contains no credentials, default is ANONYMOUS.
            If the broker URL does contain credentials, default is 
            'PLAIN DIGEST-MD5'
            '''
            self.broker_uri = broker_uri
            self.sasl_mech_list = get_sasl_mechanisms(broker_uri, 
                                                      sasl_mech_list)

            # A wallaby Store object
            self._store = None

            # A QMF broker
            self._broker = None

            # The cache maintenance thread
            self._maintain_cache = None

            # Stop the maintenance thread
            self._stop = False

            # Cached data.  Each of the keys in this dictionary is the name of
            # an attribute on the Wallaby Store object, with the exception of
            # WBTypes.TAGS.  The TAGS data is a subset of the GROUPS produced
            # in this module.
            self._cache = {WBTypes.NODES:    self.CacheData(refresh_interval), 
                           WBTypes.GROUPS:   self.CacheData(refresh_interval),
                           WBTypes.FEATURES: self.CacheData(refresh_interval),
                           WBTypes.TAGS:     self.CacheData(refresh_interval,
                                                          synthetic=self._generate_tag_data)}

            # Cache a list of nodes that are members of a tag
            self._nodes_by_tag = dict()

            # Store the name of the partition group so we can filter it out
            # of tags/groups that we return
            self._partition_group = None

            # Lock is used for synchronization with the caching thread and
            # for thread safety of any and all data that could be accessed
            # by multiple threads.
            self._lock = Lock()
            self._condition = Condition(self._lock)

        def start(self, retry_secs=5):
            '''
            Start the caching thread.

            This thread will attempt to connect to the broker and retrieve
            a Store object from the Wallaby agent.  If successful, it will 
            periodically retrieve and cache data from Wallaby.

            Only one caching thread may run at a time.  The thread may
            be restarted if it has previously been stopped.

            Note, for the moment start() and stop() are not thread safe.  They
            should only be called from a single thread.

            retry_secs -- how often the caching thread will retry failed
            operations.  This includes attempts to connect to the broker
            and retrieve a Store object as well as calls to Wallaby that
            return no data.
            '''
            # The connection to the broker can actually take a long
            # time to complete. We don't want to hang a calling function, 
            # so we handle the connection and retrieval of the 
            # initial Store object from Wallaby in a thread.
            # (There may need to be more work here if the broker or wallaby
            # going away and coming back causes a problem, but with 
            # manageConnections=True and well-known agent/object ids for
            # Wallaby it appears to recover on its own...)

            # Similarly, getting node lists etc may take a long time
            # especially over a slow network.  So we use the same thread
            # to retrieve things like node lists at defined intervals.

            # 'self' here is really a term of art since this is a local
            # function, but it refers to the WallabyOperations object
            # so the code reads nicely
            def maintain_cache(self):

                # Get initinal connection and Store obect
                self.session = Session(manageConnections=True)
                self.broker = self.session.addBroker(self.broker_uri, mechanisms=self.sasl_mech_list)
                while not self._stop:
                    self._store = self._get_store()
                    if self._store is not None:
                        setup(self._store)
                        self._partition_group = self._store.getPartitionGroup().name
                        log.debug("WallabyOperations: found wallaby store object")
                        break

                    # Check stop inside the lock to make sure that we don't miss
                    # a signal or a "stop" that was set while we were iterating.
                    self._condition.acquire()
                    if not self._stop:
                        self._condition.wait(retry_secs)
                    self._condition.release()

                # Init remaining time til next update to 0 for each
                # cached item in case the thread was restarted
                for attr, val in self._cache.iteritems():
                    val.remaining = 0

                # Okay, now we're ready to retrieve data
                while not self._stop:
                    start_processing = time.time()
                    for attr, val in self._cache.iteritems():
                        if self._stop:
                            break

                        # val.remaining is the number of seconds left before
                        # the next update of this data item.  None is "forever".
                        # Synthetic items are not retreived from the store.
                        if not val.synthetic and \
                           val.remaining is not None and val.remaining <= 0:
                            d = get_values(attr, getattr, self._store, attr, [])
                            # If the data is empty, _set_cache will leave the
                            # remaining field set to 0 for the attribute so we
                            # will try to get it again on our next retry.
                            # Otherwise, remaining will be reset to the full
                            # interval for this attribute.
                            self._set_cache(attr, d)

                    # Now handle the synthetics.  val.synthetic generates
                    # and stores it's own results.
                    for attr, val in self._cache.iteritems():
                        if self._stop:
                            break

                        if val.synthetic and \
                           val.remaining is not None and val.remaining <= 0:
                            get_values(attr, val.synthetic, *val.args)
                            
                    log.debug("WallabyOperations: total refresh processing time %s" \
                              % (time.time() - start_processing))

                    # Find out how long we should sleep for.
                    # Based on min remaining times for all items
                    # If minimum is 0 because we have items waiting
                    # for a retry, we fall back on retry_secs as a minimum.
                    sleep_time = self._find_min_remaining(min=retry_secs)

                    self._condition.acquire()
                    if not self._stop:
                        # Could be signaled, so track the actual sleep time
                        log.debug("WallabyOperations: cache thread sleeping for"\
                                  " %s seconds" % sleep_time)
                        bed_time = time.time()
                        self._condition.wait(sleep_time)
                        slept = time.time() - bed_time
                        log.debug("WallabyOperations: cache thread slept for"\
                                  " %s seconds" % slept)

                        # When we wake up from sleep here, we already
                        # have the lock so we might as well check refresh
                        # and adjust the "remaining" values
                        for attr, val in self._cache.iteritems():
                            if val.refresh: # Force an update
                                val.remaining = 0
                                val.refresh = False
                            elif val.remaining is not None:
                                val.remaining -= slept
                    self._condition.release()

                # Clear cache if we have been stopped....
                for attr in self._cache:
                    self._set_cache(attr, [])
                self._store = None

                # Have to clean up the broker
                try:
                    self.session.delBroker(self.broker)
                except:
                    pass

            #end maintain_cache

            def get_values(attr, call, *args):
                log.debug("WallabyOperations: refreshing %s" % attr)
                try:
                    # Wallaby API uses extensions to __getattr__ on 
                    # the Store to retrieve objects from the Broker 
                    # and return a list of proxy objects.
                    start = time.time()
                    d = call(*args)
                except:
                    d = []
                delta = time.time() - start
                log.debug("WallabyOperations: %s seconds to refresh %s" % (delta, attr)) 
                return d

            # Wrap the entire cache thread with an exception handler
            def wrap_maintain_cache():
               try:
                  maintain_cache(self)
                  log.debug("WallabyOperations: cache maintenance thread exited")
               except:
                  pass

            if self._maintain_cache is not None and \
               self._maintain_cache.isAlive():
                # No, you can't start another one.
                return False

            self._stop = False

            if self.broker_uri is not None:
#              self._maintain_cache = CallThread(cProfile.runctx('maintain_cache(self)', globals(), locals(), filename='sage.stats'), None)
               self._maintain_cache = CallThread(wrap_maintain_cache, None)
               self._maintain_cache.daemon = True
               self._maintain_cache.start()
               log.debug("WallabyOperations: start cache maintenance thread")
               return True
            return False

        def stop(self, wait=False, timeout=None):
            '''
            Stop the caching thread.

            Wake the caching thread if asleep and cause it to exit.
            The thread may be restarted again with a call to start()
            once it has successfully exited.  On exit, the thread will
            null out cached data.

            wait -- if True the call will block until the thread exits or
            "timeout" seconds has passed if "timeout" is not None.

            timeout -- how long to wait for the thread to exit if "wait" is True.
            A value of None means wait forever.

            Note, for the moment start() and stop() are not thread safe.  They
            should only be called from a single thread.
            '''
            if self._maintain_cache is not None:
                self._condition.acquire()
                self._stop = True
                self._condition.notify()
                self._condition.release()
                if wait and self._maintain_cache.isAlive():
                    log.debug("WallabyOperations: waiting for cache maintenance thread to exit")
                    self._maintain_cache.join(timeout)
                log.debug("WallabyOperations: stopped cache maintenance thread")

        def refresh(self, *items):
            '''
            Wake the caching thread if asleep and cause it to iterate.

            items -- what data to refresh.  If "items" is an empty
            tuple, refresh all data otherwise refresh only the data specified.
            Attributes of WBTypes define valid values for elements of "items"
            '''
            self._condition.acquire()
            try:
                if len(items) == 0:
                    do_notify = True
                    for attr, val in self._cache.iteritems():
                        val.refresh = True
                else:
                    do_notify = False
                    for attr in items:
                        if attr in self._cache:
                            do_notify = True
                            self._cache[attr].refresh = True
                if do_notify:
                    self._condition.notify()
            finally:
                self._condition.release()

        def get_data(self, which, valuefilter=None):
            '''
            Return a list of cached values for the specified category.

            The values returned will be proxy objects constructed by
            the Wallaby client library.

            which -- specifies the category.  Attributes of WBTypes 
            define valid values for "which"
            '''
            d = []
            self._lock.acquire()
            try:
                if which in self._cache:
                    d = self._cache[which].data.values()
                # Here we handle the possible filtering of node names
                if which == WBTypes.NODES:
                    if valuefilter is not None and valuefilter["nodeName"] != "%%%":
                        filter = valuefilter["nodeName"].replace("%", "")
                        if filter != "":
                            d = [value for value in d if value.name.find(filter) > -1]
            finally:
                self._lock.release()
            return d

        def get_names(self, which):
            '''
            Return a list of cached names for the specified category.

            The values returned will be the names of objects constructed
            by the Wallaby client library.

            which -- specifies the category.  Attributes of WBTypes 
            define valid values for "which"
            '''
            d = []
            self._lock.acquire()
            try:
                if which in self._cache:
                    d = self._cache[which].data.keys()
            finally:
                self._lock.release()
            return d            

        def get_node_by_name(self, name):
            '''
            Return a cached wallaby.Node object by name.

            If name does not designate a currently cached
            object, None is returned.
            '''
            return self._lookup_by_name(WBTypes.NODES, name)

        def get_group_by_name(self, name):
            '''
            Return a cached wallaby.Group object by name.

            If name does not designate a currently cached
            object, None is returned.
            '''
            return self._lookup_by_name(WBTypes.GROUPS, name)

        def get_tag_by_name(self, name):
            '''
            Return a cached wallaby.Tag object by name.

            If name does not designate a currently cached
            object, None is returned.
            '''
            return self._lookup_by_name(WBTypes.TAGS, name)

        def get_feature_by_name(self, name):
            '''
            Return a cached wallaby.Feature object by name.

            If name does not designate a currently cached
            object, None is returned.
            '''
            return self._lookup_by_name(WBTypes.FEATURES, name)

        def get_node_names(self, tag):
            '''
            Return a list of node names associated with the tag.

            The return result is a list containing the names of nodes
            in the tag group.
            '''
            names = []
            if type(tag) in (str, unicode):
                n = tag
            else:
                n = tag.name
            self._lock.acquire()
            try:
                if n in self._nodes_by_tag:
                    names =  self._nodes_by_tag[n]
            finally:
                self._lock.release()
            return names

        def get_tag_names(self, node):
            '''
            Return a list of tag names associated with the node.

            The return result is a list containing the names of tags
            on the specified node.
            '''
            names = []
            n = None
            if type(node) in (str, unicode):
                n = node
            elif hasattr(node, "name"):
                n = node.name
            if n is None:
               log.debug("WallabyOperations: get_tag_names(), parameter 'node' yields no name, returning []")
            else:
               self._lock.acquire()
               try:
                  if n in self._cache[WBTypes.NODES].data:
                     names = self._cache[WBTypes.NODES].data[n].getTags()
               finally:
                  self._lock.release()
            return names
  
        def create_tags(self, names):
            '''
            Create new tags in the Wallaby store.

            Refresh the cached lists of groups and tags.
            '''
            if self._store is None:
                log.debug("WallabyOperations: create_tag, store object not yet created")
                return False
            try:
                self._lock.acquire()
                try:                    
                    for name in names:
                        self._store.addTag(name)
                except Exception, e:
                    log.debug("WallabyOperations: create_tag, exception suppressed, %s" % str(e))
                    return False
            finally:
                self._lock.release()
            return True

        def remove_tags(self, names):
            '''
            Remove a set of tags from the Wallaby store.

            Check the cached list of tags for the
            tag name first.  Refresh cached lists of
            groups, tags, and nodes.
            '''
            if self._store is None:
                log.debug("WallabyOperations: remove_tag, store object not yet created")
                return False

            for name in names:
                if self.get_tag_by_name(name) is not None:
                    try:
                        self._store.removeGroup(name)
                    except Exception, e:
                        log.debug("WallabyOperations: remove_tag, exception suppressed, %s" % str(e))
                        return False
            return True

        def edit_tags(self, node, *tags):
            '''
            Replace existing tags on a node with the specified tags.

            node -- a wallaby.Node object or the name of a wallaby.Node object

            tags -- the new set of tags for the node, 
                    list or tuple of strings
            '''
            status = False
            if type(node) in (str, unicode):
                n = node
            else:
                n = node.name
            self._lock.acquire()
            try:
                n = n in self._cache[WBTypes.NODES].data and \
                    self._cache[WBTypes.NODES].data[n] or None
            finally:
                self._lock.release()
            if n is None:
                log.debug("WallabyOperations: edit_tags, node not found %s" % str(n))
            else:
                try:
                    try:
                        # cast to list in case tags is a tuple, list required
                        start = time.time()
                        self._lock.acquire()
                        n.modifyTags("REPLACE", list(tags), create_missing_tags=True)
                        n.update()
                        status = True
    
                        delta = time.time() - start
                        log.debug("WallabyOperations: edit_tags %s" % delta)
                    except Exception, e:
                        log.debug("WallabyOperations: edit_tags, exception suppressed, %s" % str(e))
                finally:
                    self._lock.release()
            return status

        def edit_features(self, group, *features):
            '''
            Replace existing features in a group with the specified features.

            group -- a wallaby.Group object or the name of a wallaby.Group object

            features -- the new set of features for the group, 
                        list or tuple of strings
            '''
            status = False
            if type(group) in (str, unicode):
                g = group
            else:
                g = group.name
            self._lock.acquire()
            try:
                g = g in self._cache[WBTypes.GROUPS].data and \
                    self._cache[WBTypes.GROUPS].data[g] or None
            finally:
                self._lock.release()
            if g is None:
                log.debug("WallabyOperations: edit_features, group not found %s" % str(g))
            else:
                try:
                    start = time.time()
                    g.modifyFeatures("REPLACE", features)
                    g.update()
                    status = True
                    delta = time.time() - start
                    log.debug("WallabyOperations: edit_features %s" % delta)
                except Exception, e:
                    log.debug("WallabyOperations: edit_features, exception suppressed, %s" % str(e))
            return status

        def set_interval(self, which, refresh):
            '''
            Set an individual refresh interval for a data item.

            The interval set here will override the initial default
            interval for the item created in WallabyOperations' constructor.

            which -- specifies the data item.  Attributes of WBTypes 
            define valid values for "which"

            refresh -- the interval in seconds.  If None, the specified item
            will be updated iff refresh() is called.
            '''
            if which in self._cache:
                self._lock.acquire()
                self._cache[which].interval = refresh
                self._lock.release()

        def activate_configuration(self):
            '''
            Call activateConfiguration on the store object.
            Returns None if the store is not valid, otherwise
            returns result of store.activateConfiguration.
            '''
            if self._store is not None:
                return self._store.activateConfiguration()
            else:
                log.debug("WallabyOperations: activate_configuration," \
                          " store object not yet created")

        def validate_configuration(self):
            '''
            Call validateConfiguration on the store object.
            Returns None if the store is not valid, otherwise
            returns result of store.validateConfiguration.
            '''
            if self._store is not None:
                return self._store.validateConfiguration()
            else:
                log.debug("WallabyOperations: validate_configuration," \
                          " store object not yet created")

        def is_store_valid(self):
            '''
            Return True if contact has been made with the Wallaby agent
            and a store object has been created.
            '''
            return self._store is not None

# Super secret private implementation stuff.  Don't look!

        def _find_min_remaining(self, min):
            # None indicates forever, the biggest value
            # Note though that None < int is True in Python!
            t = None 
            for attr, val in self._cache.iteritems():
                if t == None or \
                   (val.remaining is not None and val.remaining < t):
                    t = val.remaining

            # Put a floor on this
            if t is not None and t < min:
                t = min
            return t
            
        def _get_store(self):
            # Ideally there should only be a single Store object from a single agent.
            # We constrain the search a bit, hopefully more efficient
            store = None
            try:
                agents = [agent for agent in self.session.getAgents() \
                          if "com.redhat.grid.config:Store" in agent.label]
                for agent in agents:
                    s = self.session.getObjects(_agent = agent, _class = "Store")
                    if len(s) > 0:
                        # And finally wrap the QMF object in a wallaby.Store wrapper
                        store = wallaby.Store(s[0], self.session)
                        break
            except:
                pass
            return store

        def _generate_tag_data(self):
           # figure out the tag list and nodes per tag
            groups = self.get_data(WBTypes.GROUPS)
            tags = []
            nodes_by_tag = dict()
            for g in groups:
                if not g.name.startswith("+++") and \
                   self._store.isTag(g):
                    tags.append(g)
                    nodes = g.membership()
                    nodes_by_tag[g.name] = nodes

            self._lock.acquire()
            try:
                self._cache[WBTypes.TAGS].data = self._to_dict(tags)
                self._cache[WBTypes.TAGS].reset_remaining(len(tags) == 0)
                self._nodes_by_tag = nodes_by_tag
            finally:
                self._lock.release()
            log.debug("WallabyOperations: %s list updated (%s items)" % (WBTypes.TAGS, len(tags)))

        def _set_cache(self, attr, data):
            self._lock.acquire()
            try:
                self._cache[attr].data = self._to_dict(data)
                self._cache[attr].reset_remaining(len(data) == 0)
            finally:
                self._lock.release()
            log.debug("WallabyOperations: %s list updated (%s items)" % (attr, len(data)))

        def _to_dict(self, data):
            return dict([(x.name, x) for x in data])

        def _lookup_by_name(self, which, name):
            n = None
            self._lock.acquire()
            try:
                if name in self._cache[which].data:
                    n = self._cache[which].data[name]
            finally:
                self._lock.release()
            return n

        class CacheData(object):
            def __init__(self, interval, synthetic=False, args=()):
                # These attributes are only referenced from the cache thread
                # so they do not need to be protected
                self.remaining = 0
                self.synthetic = synthetic
                self.args = args

                # Use of these these items need to be protected by the lock
                self.refresh = False
                self.interval = interval
                self.data = {}

            def reset_remaining(self, retry):
                # If retry is True, we want to try to get the data
                # at the next opportunity, otherwise we will wait.
                if retry:
                    self.remaining = 0
                else:
                    self.remaining = self.interval

else:
    class WallabyOperations(object):
        '''
        Dummy object when wallaby imports fail
        '''
        def __init__(self, *args, **kwargs):
            pass

        def start(self, *args, **kwargs):
            log.debug("WallabyOperations: uing dummy implementation, imports failed")
            return False

        def stop(self, *args, **kwargs):
            pass

        def refresh(self, *args, **kwargs):
            pass

        def get_data(self, *args, **kwargs):
            return []

        def get_names(self, *args, **kwargs):
            return []

        def get_node_by_name(self, *args, **kwargs):
            return None

        def get_group_by_name(self, *args, **kwargs):
            return None

        def get_tag_by_name(self, *args, **kwargs):
            return None

        def get_feature_by_name(self, *args, **kwargs):
            return None

        def get_node_names(self, *args, **kwargs):
            return []

        def get_tag_names(self, *args, **kwargs):
            return []

        def create_tags(self, *args, **kwargs):
            return False

        def remove_tags(self, *args, **kwargs):
            return False

        def edit_tags(self, *args, **kwargs):
            return False

        def edit_features(self, *args, **kwargs):
            return False

        def set_interval(self, *args, **kwargs):
            pass
        
        def activate_configuration(self, *args, **kwargs):
            return None

        def validate_configuration(self, *args, **kwargs):
            return None

        def is_store_valid(self):
            return False

        
