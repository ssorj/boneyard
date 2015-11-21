import copy
import resource
import pickle
from rosemary.sqltype import qmf_type_code_by_string

from psycopg2 import IntegrityError, TimestampFromTicks
from psycopg2.extensions import cursor as Cursor
from rosemary.model import *

from mint.model import *
from mint.util import *

log = logging.getLogger("mint.plumage.update")

sample_window_min = 60
sample_window_max = 60 * 5

class UpdateDropped(Exception):
    pass

class MappingException(Exception):
    pass

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
                        cls.delete_sample_selection(self.cursor)
                    self.cursor.connection.commit()
                else:
                    log.debug("Skipping persistent class " + str(cls))

        if len(self.app.classes):
            log.debug("Delete all objects by bound classes " +\
                          str(self.app.classes))
            for cls in self.app.classes:
                loop_body(cls)
        else:
            log.debug("Delete all objects by bound packages " +\
                          str(self.app.packages))
            for pkg in self.app.packages:
                for cls in pkg._classes:
                    loop_body(cls)

    def init(self):
        self.conn = self.app.database.get_connection()

        self.cursor = self.conn.cursor(cursor_factory=UpdateCursor)
        self.cursor.stats = self.stats

    def get_first_and_last_sample_timestamp(self, cls):        
        cursor = self.conn.cursor()
        table = cls.sql_samples_table
        oldest = None
        newest = None
        cursor.execute("select %s from %s order by %s asc limit 1" % (cls.timestamp, table.identifier, cls.timestamp)) 
        if cursor.rowcount > 0:
            oldest = cursor.fetchone()[0]
        
        cursor.execute("select %s from %s order by %s desc limit 1" % (cls.timestamp, table.identifier, cls.timestamp))
        if cursor.rowcount > 0:
            newest = cursor.fetchone()[0]
        
        return (oldest, newest)

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

            self.stats.dequeued += 1

            update.process(self)

class UpdateStats(object):

    def __init__(self, app):
        self.enqueued = 0
        self.dequeued = 0
        self.dropped = 0

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
        
class UpdateCursor(Cursor):
    def execute(self, sql, args=None):
        super(UpdateCursor, self).execute(sql, args)

        self.stats.sql_ops += 1

class Update(object):
    def __init__(self, model, cls):
        self.model = model
        self.cls = cls

    def process(self, thread):
        log.debug("Processing %s", self)
        try:
            self.do_process(thread.cursor, thread.stats) 
            thread.conn.commit()
        except UpdateDropped:
            log.debug("Update dropped")

            thread.conn.rollback()

            thread.stats.dropped += 1
        except:
            log.debug("Update failed", exc_info=True)

            thread.conn.rollback()

            thread.stats.errors += 1

            if thread.halt_on_error:
                raise

    def do_process(self, cursor, stats):
        raise Exception("Not implemented")

    def __repr__(self):
        return self.__class__.__name__

class ObjectUpdate(Update):
    def __init__(self, model, plumage_object, cls):
        super(ObjectUpdate, self).__init__(model, cls)

        self.plumage_object = plumage_object

    def do_process(self, cursor, stats):
        # Okay, we want to do a lookup by object id here.
        # Let the class find the unique identifiers in the
        # object based on the xml table description and do 
        # the lookup for us.  Names in the record must match
        # the names in the xml, or we need a mapping construct
        # in the rosemary.xml to override.
        sig = self.cls.get_signature(self.plumage_object)
        try:
            obj = self.cls.get_object_by_signature(cursor, sig)
        except:
            self.create_object(cursor, stats, self.cls)
            return

        self.update_object(cursor, stats, obj)

    def create_object(self, cursor, stats, cls):
        obj = cls.create_object(cursor)

        object_columns = list()
        sample_columns = list()

        table = cls.sql_table

        object_columns.append(table._id)

        self.process_properties(obj, object_columns)
        self.process_statistics(obj, object_columns, sample_columns)

        statements = list()

        sql = cls.sql_insert_object.emit(object_columns)
        statements.append(sql)

        if sample_columns:
            sql = cls.sql_samples_insert.emit(sample_columns)
            statements.append(sql)
            obj._sample_time = time.time()

        sql = "; ".join(statements)
        self.execute_sql(cursor, sql, obj.__dict__)
        obj._save_time = datetime.now()
        self.model.print_event(3, "Created %s", obj)

        stats.objects_created += 1
        #stats.objects_created_by_class[cls] += 1

        return obj

    def update_object(self, cursor, stats, obj):
        object_columns = list()
        sample_columns = list()

        self.process_properties(obj, object_columns)
        self.process_statistics(obj, object_columns, sample_columns)

        statements = list()
        cls = obj._class

        if object_columns:
            sql = cls.sql_update_object.emit(object_columns)
            statements.append(sql)

        if sample_columns:
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

    def process_properties(self, obj, columns):
        cls = obj._class

        # get a list of property names from the cls
        # loop through the list of properties, look for
        # the value in the object
        for name, prop in cls._properties_by_name.iteritems():
            value = getattr(self.plumage_object, name)
            if value is not None:
                value = transform_value(prop, value)
            if value == getattr(obj, prop.sql_column.name):
                continue

            setattr(obj, prop.sql_column.name, value)
            columns.append(prop.sql_column)

    def process_statistics(self, obj, update_columns, insert_columns):
        build_columns = list()
        saw_change = False
        cls = obj._class

        # get a list of statistic names from the cls
        # loop through the list of properties, look for
        # the value in the object
        for name, stat in cls._statistics_by_name.iteritems():
            value = getattr(self.plumage_object, name)
            if value is not None:
                value = transform_value(stat, value)

            # Don't write unchanged values
            if value != getattr(obj, stat.sql_column.name):
                setattr(obj, stat.sql_column.name, value)
                update_columns.append(stat.sql_column)
                saw_change = True

            # If we do end up seeing a value change, we will
            # need to insert an entire row so build it up
            build_columns.append(stat.sql_column)

        if saw_change:
            # Okay, we saw some changed statistics.  We also
            # need to include here all the property columns marked 
            # unique since they are reflected in the sample tables
            # in addition to the statistics.
            key_cols = []
            for p in cls._properties:
                if p.unique:
                    key_cols.append(p.sql_column)

            insert_columns.extend(key_cols)
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

            log.error("object properties:")

            # see process_properties
            #for item in sorted(self.qmf_object.getProperties()):
            #    log.error("    %-34s  %r", *item)

            #log.error("object statistics:")

            # see process statistics
            #for item in sorted(self.qmf_object.getStatistics()):
            #    log.error("    %-34s  %r", *item)

            raise

    def __repr__(self):
        name = self.__class__.__name__
        return name

        #agent_id = self.get_agent_id()
        #cls = self.qmf_object.getClassKey().getClassName()
        #obj_id = self.get_object_id()

        #return "%s(%s,%s,%s)" % (name, agent_id, cls, obj_id)

class MappingException(Exception):
    pass

def transform_default(value):
    return value

def transform_timestamp(value):
    if value != 0:
        if isinstance(value,datetime):
            return value
        else:
            return datetime.fromtimestamp(value / 1000000000)

def transform_pickle(value):
    return pickle.dumps(x)

transformers = list([transform_default for x in range(32)])

transformers[8] = transform_timestamp
transformers[10] = str
transformers[14] = str
transformers[15] = transform_pickle

def transform_value(attr, value):
    t = qmf_type_code_by_string[attr.type]
    return transformers[t](value)
