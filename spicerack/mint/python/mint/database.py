import psycopg2

from util import *

log = logging.getLogger("mint.database")

class MintDatabase(object):
    def __init__(self, app, dsn):
        self.app = app
        self.dsn = dsn

    def get_connection(self):
        return psycopg2.connect(self.dsn)

    def check(self):
        log.info("Checking %s", self)
        # checks moved to init because the model has to be
        # initialized before we can check the schema.  And
        # there is no point connecting to the database twice...

    def init(self):
        log.info("Initializing %s", self)
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            self.check_connection(cursor)
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

    def check_connection(self, cursor):
        cursor.execute("select now()")
        log.debug("Database is talking at '%s'", self.dsn)

    def __repr__(self):
        return self.__class__.__name__
