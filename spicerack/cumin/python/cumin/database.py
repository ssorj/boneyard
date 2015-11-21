import psycopg2
import re
import threading

from psycopg2.extensions import *

from util import *

log = logging.getLogger("cumin.database")

class CuminDatabase(object):
    def __init__(self, app, dsn):
        self.app = app
        self.dsn = dsn

        self.connection_args = dict()
        self.thread_local = threading.local()

    def init(self, schema_version_check):
        log.info("Initializing %s", self)

        #m = re.match(r"^([^:]+)://([^@]+)@([^/]+)/(.+)$", self.uri)
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            self.check_connection(cursor)
            if schema_version_check:
                self.app.admin.check_schema(cursor)
            conn.close()
        except psycopg2.OperationalError:
            conn and conn.close()
            log.error("Connection to database failed, is the database running?")
            raise
        except Exception, e:
            conn and conn.close()
            log.error(str(e))
            raise

    def check(self):
        # checks moved to init because the model has to be
        # initialized before we can check the schema.  And
        # there is no point connecting to the database twice...
        log.info("Checking %s", self)

    def check_connection(self, cursor):
        cursor.execute("select now()")
        log.debug("Database is talking at '%s'", self.dsn)

    def get_connection(self):
        return psycopg2.connect(self.dsn)

    def get_read_connection(self):
        key = "read_connection"
        conn = getattr(self.thread_local, key, None)

        if not conn or conn.closed:
            conn = self.get_connection()
            setattr(self.thread_local, key, conn)

            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        return conn

    def get_read_cursor(self):
        return self.get_read_connection().cursor()

    def __repr__(self):
        return self.__class__.__name__

