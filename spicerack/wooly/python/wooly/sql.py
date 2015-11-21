from resources import *
from template import *
from util import *
from wooly import *

strings = StringCatalog(__file__)
log = logging.getLogger("wooly.sql")

class SqlOperation(object):
    def __init__(self, app):
        super(SqlOperation, self).__init__()

        self.app = app

        sql_string = self.get_string("sql")
        self.sql_tmpl = ObjectTemplate(self, sql_string)

    # XXX instead of this, make the lookup logic on Widget generic and
    # use it here as well
    def get_string(self, key):
        cls = self.__class__
        module = sys.modules[cls.__module__]
        strs = module.__dict__.get("strings")

        if strs:
            return strs.get(cls.__name__ + "." + key)

    def get_connection(self, session):
        pass

    def do_execute(self, session, sql):
        conn = self.get_connection(session)

        if not conn:
            raise Exception("Database error")
            
        cursor = conn.cursor()

        log.debug("Query: \n%s", sql)

        cursor.execute(sql)

        return cursor

    def execute(self, session):
        sql = self.render_sql(session)

        return self.do_execute(session, sql)

    def render_sql(self, session):
        writer = Writer()
        self.sql_tmpl.render(writer, session)
        return writer.to_string()

class SqlDataSet(SqlOperation):
    def __init__(self, app):
        super(SqlDataSet, self).__init__(app)

        count_sql_string = self.get_string("count_sql")

        self.count_sql_tmpl = ObjectTemplate(self, count_sql_string)

        self.where_exprs = SessionAttribute(self, "where")

        self.limit = SessionAttribute(self, "limit")
        self.limit.default = "all"

        self.offset = SessionAttribute(self, "offset")
        self.offset.default = 0

    def add_where_expr(self, session, expr, *args):
        exprs = self.where_exprs.get(session)
        exprs.append(expr % args)

    def get_connection(self, session):
        pass

    def get_items(self, session):
        return self.execute(session).fetchall()

    def do_execute(self, session, sql):
        conn = self.get_connection(session)

        if not conn:
            raise Exception("Database error")
            
        cursor = conn.cursor()

        log.debug("Query: \n%s", sql)

        cursor.execute(sql)

        return cursor

    def execute(self, session):
        sql = self.render_sql(session)

        return self.do_execute(session, sql)

    def count(self, session):
        sql = self.render_count_sql(session)
        values = self.values.get(session)

        cursor = self.do_execute(session, sql, values)
        data = cursor.fetchone()

        return data[0]

    def render_sql(self, session):
        writer = Writer()
        self.sql_tmpl.render(writer, session)
        return writer.to_string()

    def render_count_sql(self, session):
        writer = Writer()
        self.count_sql_tmpl.render(writer, session)
        return writer.to_string()

    def render_sql_where(self, session):
        exprs = self.where_exprs.get(session)
        if exprs:
            return "where %s" % " and ".join(exprs)

    def render_sql_order_by(self, session):
        pass

    def render_sql_limit(self, session):
        limit = self.limit.get(session)
        offset = self.offset.get(session)

        return "limit %s offset %i" % (str(limit), offset)
