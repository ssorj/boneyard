import copy
import resource
import pickle

from psycopg2 import IntegrityError, TimestampFromTicks
from psycopg2.extensions import cursor as Cursor
from rosemary.model import *

from model import *
from util import *

log = logging.getLogger("mint.update")

sample_window_min = 60
sample_window_max = 60 * 5

class UpdateThread(MintDaemonThread):
    def __init__(self, app):
        super(UpdateThread, self).__init__(app)

        self.updates = ConcurrentQueue(maxsize=1000)
        self.stats = UpdateStats(self.app)

        self.conn = None
        self.cursor = None

        self.halt_on_error = False

        # For timestamp persistent data, if this flag is True,
        # we will delete the objects and samples on startup.
        # This is to allow purging of large data sets.
        self.del_on_start = False

    def _delete_all_objects(self):
        def loop_body(cls):
            if cls._storage != "none":
                persistent = cls.check_persistent()
                if (persistent == "session") or \
                   (persistent == "timestamp" and self.del_on_start):
                    cls.delete_selection(self.cursor)
                    if persistent == "timestamp":
                        # del_on_start must be true...
                        cls.delete_sample_selection(self,cursor)
                    self.cursor.connection.commit()
                else:
                    log.debug("Skipping persistent class " + str(cls))

        if len(self.app.qmf_classes):
            log.debug("Delete all objects by bound classes " +\
                          str(self.app.qmf_classes))
            for cls in self.app.qmf_classes:
                loop_body(cls)
        else:
            # We bound all classes.  Loop over model
            log.debug("Delete all objects by bound packages " +\
                          str(self.app.qmf_packages))
            for pkg in self.app.qmf_packages:
                for cls in pkg._classes:
                    loop_body(cls)

    def init(self):
        self.conn = self.app.database.get_connection()

        self.cursor = self.conn.cursor(cursor_factory=UpdateCursor)
        self.cursor.stats = self.stats

    def enqueue(self, update):
        self.updates.put(update)

        self.stats.enqueued += 1

    def run(self):
        self._delete_all_objects()

        while True:
            if self.stop_requested:
                break
            try:
                update = self.updates.get(True, 1)
            except Empty:
                continue
            if self.stop_requested:
                break

            self.stats.dequeued += 1

            update.process(self)

class UpdateStats(object):
    group_names = ("Updates", "Agents", "Objects")
    groups = "%43s | %32s | %32s |" % group_names

    heading_names = \
        ("Depth", "*Enqueued", "*Dequeued", "*Dropped",
         "*Created", "*Updated", "*Deleted",
         "*Created", "*Updated", "*Deleted",
         "*Sql Ops", "Errors", "Cpu (%)", "Mem (M)")
    headings_fmt = \
        "%10s %10s %10s %10s | " + \
        "%10s %10s %10s | " + \
        "%10s %10s %10s | " + \
        "%10s %10s %10s %10s"
    headings = headings_fmt % heading_names


    values_fmt = \
        "%10i %10.1f %10.1f %10.1f | " + \
        "%10.1f %10.1f %10.1f | " + \
        "%10.1f %10.1f %10.1f | " + \
        "%10.1f %10i %10i %10.1f"

    then = None
    now = None

    def __init__(self, app):
        self.enqueued = 0
        self.dequeued = 0
        self.dropped = 0

        self.agents_created = 0
        self.agents_updated = 0
        self.agents_deleted = 0

        self.objects_created = 0
        self.objects_updated = 0
        self.objects_deleted = 0

        self.objects_created_by_class = defaultdict(int)
        self.objects_updated_by_class = defaultdict(int)
        self.objects_deleted_by_class = defaultdict(int)

        self.sql_ops = 0
        self.errors = 0

        self.time = None
        self.cpu = 0
        self.memory = 0

    def capture(self):
        now = copy.copy(self)

        now.time = time.time()

        rusage = resource.getrusage(resource.RUSAGE_SELF) 

        now.cpu = rusage[0] + rusage[1]
        now.memory = self.get_resident_pages() * resource.getpagesize()

        UpdateStats.then = UpdateStats.now
        UpdateStats.now = now

    def get_resident_pages(self):
        try:
            line = open("/proc/%i/statm" % os.getpid()).read()
        except:
            return 0

        return int(line.split()[1])

    def print_headings(self):
        print self.groups
        print self.headings

    def print_values(self):
        self.capture()

        if not self.then:
            return

        values = [self.now.enqueued - self.then.enqueued,
                  self.now.dequeued - self.then.dequeued,
                  self.now.dropped - self.then.dropped,
                  self.now.agents_created - self.then.agents_created,
                  self.now.agents_updated - self.then.agents_updated,
                  self.now.agents_deleted - self.then.agents_deleted,
                  self.now.objects_created - self.then.objects_created,
                  self.now.objects_updated - self.then.objects_updated,
                  self.now.objects_deleted - self.then.objects_deleted,
                  self.now.sql_ops - self.then.sql_ops]

        # self.now.dropped - self.then.dropped,

        secs = self.now.time - self.then.time
        values = map(lambda x: x / secs, values)

        values.insert(0, self.now.enqueued - self.now.dequeued)

        values.append(self.errors)
        values.append(int((self.now.cpu - self.then.cpu) / secs * 100))
        values.append(self.now.memory / 1000000.0)

        print self.values_fmt % tuple(values)

    def print_values_by_class(self):
        names = ("Class", "Created", "Updated", "Deleted")
        print "%20s  %10s  %10s  %10s" % names

        for pkg in mint.model._packages:
            for cls in pkg._classes:
                created = stats.created_by_class[cls]
                updated = stats.updated_by_class[cls]
                deleted = stats.deleted_by_class[cls]

                if created or updated or deleted:
                    args = (cls._name, created, updated, deleted)
                    print "%-20s  %10i  %10i  %10i" % args
        
class UpdateCursor(Cursor):
    def execute(self, sql, args=None):
        super(UpdateCursor, self).execute(sql, args)

        self.stats.sql_ops += 1

class Update(object):
    def __init__(self, model):
        self.model = model

    def process(self, thread):
        log.debug("Processing %s", self)

        try:
            self.do_process(thread.cursor, thread.stats, 
                            thread.app.qmf_classes, thread.app.qmf_packages)

            thread.conn.commit()
        except UpdateDropped:
            log.debug("Update dropped")

            thread.conn.rollback()

            thread.stats.dropped += 1
        except:
            log.debug("Update failed", exc_info=True)

            thread.conn.rollback()

            thread.stats.errors += 1

            #print_exc()

            if thread.halt_on_error:
                raise

    def do_process(self, cursor, stats, bound_classes, bound_packages):
        raise Exception("Not implemented")

    def __repr__(self):
        return self.__class__.__name__

class ObjectUpdate(Update):
    def __init__(self, model, qmf_object):
        super(ObjectUpdate, self).__init__(model)

        self.qmf_object = qmf_object

    def do_process(self, cursor, stats, bound_classes, bound_packages):
        cls = self.get_class()
        agent_id = self.get_agent_id()
        object_id = self.get_object_id()

        delete_time = self.qmf_object.getTimestamps()[2]

        try:
            agent = self.model.agents_by_id[agent_id]
        except KeyError:
            raise UpdateDropped()
        
        try:
            obj = agent.get_object(cursor, cls, object_id)
        except RosemaryNotFound:
            if not self.qmf_object.getProperties():
                raise UpdateDropped()

            if delete_time != 0:
                raise UpdateDropped()

            obj = self.create_object(cursor, stats, cls)

            return

        if delete_time != 0:
            self.delete_object(cursor, stats, obj)

            del agent.objects_by_id[obj._qmf_object_id]

            return

        if cls._package is self.model.org_apache_qpid_broker:
            self.maybe_drop_sample(obj)

        self.update_object(cursor, stats, obj)

    def get_agent_id(self):
        return make_agent_id(self.qmf_object.getAgent())

    def get_class(self):
        class_key = self.qmf_object.getClassKey()
        name = class_key.getPackageName()

        try:
            pkg = self.model._packages_by_name[name]
        except KeyError:
            raise UpdateDropped()

        name = class_key.getClassName()

        try:
            cls = pkg._classes_by_lowercase_name[name.lower()]
        except KeyError:
            raise UpdateDropped()

        return cls

    def get_object_id(self):
        return self.qmf_object.getObjectId().objectName

    def maybe_drop_sample(self, obj):
        properties = self.qmf_object.getProperties()
        statistics = self.qmf_object.getStatistics()

        if not properties and statistics:
            # Just stats; do we want it?
            # if stats.enqueued - stats.dequeued > 500:

            now = time.time()
            update = self.qmf_object.getTimestamps()[0] / 1000000000
            sample = obj._sample_time

            if update < now - sample_window_max:
                # The sample is too old
                raise UpdateDropped()

            if sample and sample > now - sample_window_min:
                # The samples are too fidelitous
                raise UpdateDropped()

    def create_object(self, cursor, stats, cls):
        update_time, create_time, delete_time = self.qmf_object.getTimestamps()
        create_time = datetime.fromtimestamp(create_time / 1000000000)
        update_time = datetime.fromtimestamp(update_time / 1000000000)

        obj = cls.create_object(cursor)
        obj._qmf_agent_id = self.get_agent_id()
        obj._qmf_object_id = self.get_object_id()
        obj._qmf_create_time = create_time
        obj._qmf_update_time = update_time

        object_columns = list()
        sample_columns = list()

        table = cls.sql_table

        object_columns.append(table._id)
        object_columns.append(table._qmf_agent_id)
        object_columns.append(table._qmf_object_id)
        object_columns.append(table._qmf_create_time)
        object_columns.append(table._qmf_update_time)

        self.process_properties(obj, object_columns, cursor)
        self.process_statistics(obj, object_columns, sample_columns)

        statements = list()

        sql = cls.sql_insert_object.emit(object_columns)
        statements.append(sql)

        if sample_columns:
            sample_columns.append(cls.sql_samples_table._qmf_update_time)

            sql = cls.sql_samples_insert.emit(sample_columns)
            statements.append(sql)

            obj._sample_time = time.time()

        sql = "; ".join(statements)
        self.execute_sql(cursor, sql, obj.__dict__)

        self.process_deferred_links(cursor, obj)

        obj._save_time = datetime.now()

        self.model.print_event(3, "Created %s", obj)

        stats.objects_created += 1
        #stats.objects_created_by_class[cls] += 1

        return obj

    def process_deferred_links(self, cursor, obj):
        agent = self.model.agents_by_id[obj._qmf_agent_id]

        if obj._qmf_object_id not in agent.deferred_links_by_id:
            return

        links = agent.deferred_links_by_id[obj._qmf_object_id]

        for link in links:
            link.realize(cursor, obj)

        del agent.deferred_links_by_id[obj._qmf_object_id]

    def update_object(self, cursor, stats, obj):
        update_time, create_time, delete_time = self.qmf_object.getTimestamps()
        update_time = datetime.fromtimestamp(update_time / 1000000000)

        obj._qmf_update_time = update_time

        object_columns = list()
        sample_columns = list()

        self.process_properties(obj, object_columns, cursor)
        self.process_statistics(obj, object_columns, sample_columns)

        statements = list()
        cls = obj._class

         # force a write if it's been too long, even if the values match
        if object_columns \
                or (obj._save_time != None and \
                    obj._qmf_update_time != None and \
                    obj._save_time < obj._qmf_update_time - timedelta(hours=1)):
            object_columns.append(cls.sql_table._qmf_update_time)

            sql = cls.sql_update_object.emit(object_columns)
            statements.append(sql)

            obj._save_time = datetime.now()

        if sample_columns:
            sample_columns.append(cls.sql_samples_table._qmf_update_time)

            sql = cls.sql_samples_insert.emit(sample_columns)
            statements.append(sql)

            obj._sample_time = time.time()

        if not statements:
            raise UpdateDropped()

        sql = "; ".join(statements)
        self.execute_sql(cursor, sql, obj.__dict__)

        self.model.print_event(4, "Updated %s", obj)

        stats.objects_updated += 1
        #stats.objects_updated_by_class[cls] += 1

    def delete_object(self, cursor, stats, obj):
        obj.delete(cursor)

        self.model.print_event(3, "Deleted %s", obj)

        stats.objects_deleted += 1
        #stats.objects_deleted_by_class[obj._class] += 1

    def process_properties(self, obj, columns, cursor):
        cls = obj._class

        for prop, value in self.qmf_object.getProperties():
            try:
                if prop.type == 10:
                    col, nvalue = self.process_reference \
                        (obj, prop, value, cursor)
                else:
                    col, nvalue = self.process_value(cls, prop, value)
            except MappingException, e:
                log.debug(e)
                continue

            # XXX This optimization will be obsolete when QMF does it
            # instead

            if nvalue == getattr(obj, col.name):
                continue

            setattr(obj, col.name, nvalue)
            columns.append(col)

    def process_reference(self, obj, prop, oid, cursor):
        try:
            ref = obj._class._references_by_name[prop.name]
        except KeyError:
            raise MappingException("Reference %s is unknown" % prop.name)

        if not ref.sql_column:
            raise MappingException("Reference %s has no column" % ref.name)

        value = None

        if oid:
            if oid.isV2:
                agent_id = oid.agentName
            else:
                # Not much we can do but assume same agent
                agent_id = self.get_agent_id()

            try:
                agent = self.model.agents_by_id[agent_id]
            except KeyError:
                raise MappingException("Agent %s is unknown" % agent_id)

            object_id = oid.objectName

            try:
                that = agent.get_object(cursor, ref.that_cls, object_id)
            except RosemaryNotFound:
                link = DeferredLink(obj, ref)
                agent.deferred_links_by_id[object_id].append(link)

                msg = "Deferring link to object %s %s"
                raise MappingException(msg % (ref.that_cls, object_id))

            value = that._id

        return ref.sql_column, value

    def process_value(self, cls, prop, value):
        try:
            col = cls._properties_by_name[prop.name].sql_column
        except KeyError:
            raise MappingException("Property %s is unknown" % prop)

        if value is not None:
            value = transform_value(prop, value)

        return col, value

    def process_statistics(self, obj, update_columns, insert_columns):
        build_columns = list()
        saw_change = False
        for stat, value in self.qmf_object.getStatistics():
            try:
                col = obj._class._statistics_by_name[stat.name].sql_column
            except KeyError:
                log.debug("Statistic %s is unknown", stat)

                continue

            if value is not None:
                value = transform_value(stat, value)

            # XXX hack workaround
            if col.name == "MonitorSelfTime":
                value = datetime.now()

            # Don't write unchanged values
            #
            # XXX This optimization will be obsolete when QMF does it
            # instead
            if value != getattr(obj, col.name):
                setattr(obj, col.name, value)
                update_columns.append(col)
                saw_change = True

            # If we do end up seeing a value change, we will
            # need to insert an entire row so build it up
            build_columns.append(col)

        if saw_change:        
            insert_columns.extend(build_columns)


    def execute_sql(self, cursor, text, args):
        try:
            cursor.execute(text, args)
        except:
            log.debug("%s failed sql execute", self, exc_info=True)
            log.error("Sql execute failed")
            log.error("Sql text: %s", text)
            log.error("Sql values:")

            for item in sorted(args.items()):
                log.error("    %-34s  %r", *item)

            log.error("Sql row count: %i", cursor.rowcount)

            log.error("Qmf properties:")

            for item in sorted(self.qmf_object.getProperties()):
                log.error("    %-34s  %r", *item)

            log.error("Qmf statistics:")

            for item in sorted(self.qmf_object.getStatistics()):
                log.error("    %-34s  %r", *item)

            raise

    def __repr__(self):
        name = self.__class__.__name__
        agent_id = self.get_agent_id()
        cls = self.qmf_object.getClassKey().getClassName()
        obj_id = self.get_object_id()

        return "%s(%s,%s,%s)" % (name, agent_id, cls, obj_id)

class DeferredLink(object):
    def __init__(self, this, reference):
        self.this = this
        self.reference = reference

    def realize(self, cursor, that):
        column = self.reference.sql_column
        values = {column.name: that._id, "_id": self.this._id}

        self.this._class.sql_update_object.execute(cursor, values, (column,))

        msg = "Realized deferred link to %s via %s"
        log.debug(msg, that, self.reference)

class AgentUpdate(Update):
    def __init__(self, model, qmf_agent):
        super(AgentUpdate, self).__init__(model)

        self.qmf_agent = qmf_agent

    def get_agent_id(self):
        return make_agent_id(self.qmf_agent)

    def do_process(self, cursor, stats, bound_classes, bound_packages):
        agent_id = self.get_agent_id()

        try:
            agent = self.model.agents_by_id[agent_id]
        except KeyError:
            agent = MintAgent(self.model, agent_id)
            stats.agents_created += 1
            return

        #timestamp = timestamp / 1000000000
        #agent.last_heartbeat = datetime.fromtimestamp(timestamp)

        agent.last_heartbeat = datetime.now()

        stats.agents_updated += 1

    def delete_agent_objects(self, cursor, stats, agent, 
                             bound_classes, bound_packages):

        def loop_body(cls):
            if cls._storage != "none" and cls.check_persistent() == "session":
                count = cls.delete_selection(cursor, _qmf_agent_id=agent.id)
                stats.objects_deleted += count
                #stats.objects_deleted_by_class[cls] += count
                cursor.connection.commit()

        if len(bound_classes):
            log.debug("Delete agent objects by bound classes " +\
                          str(bound_classes))
            for cls in bound_classes:
                loop_body(cls)
        else:
            # We bound all classes.  Loop over model
            log.debug("Delete agent objects by bound packages " +\
                          str(bound_packages))
            for pkg in bound_packages:
                for cls in pkg._classes:
                    loop_body(cls)

    def __repr__(self):
        name = self.__class__.__name__
        agent_id = self.get_agent_id()

        return "%s(%s)" % (name, agent_id)

class AgentDelete(AgentUpdate):
    def do_process(self, cursor, stats, bound_classes, bound_packages):
        agent_id = self.get_agent_id()

        try:
            agent = self.model.agents_by_id[agent_id]
        except KeyError:
            raise UpdateDropped()

        agent.delete()

        stats.agents_deleted += 1

        self.delete_agent_objects(cursor, stats, agent, bound_classes, bound_packages)

class UpdateDropped(Exception):
    pass

class MappingException(Exception):
    pass

def transform_default(value):
    return value

def transform_timestamp(value):
    if value != 0:
        return datetime.fromtimestamp(value / 1000000000)

def transform_pickle(value):
    return pickle.dumps(x)

transformers = list([transform_default for x in range(32)])

transformers[8] = transform_timestamp
transformers[10] = str
transformers[14] = str
transformers[15] = transform_pickle

def transform_value(attr, value):
    return transformers[attr.type](value)
