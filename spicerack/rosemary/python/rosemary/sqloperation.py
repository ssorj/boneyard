from sqlfilter import *
from sqlmodel import *
from util import *

log = logging.getLogger("rosemary.sqloperation")

class SqlOperation(object):
    def __init__(self, table):
        self.table = table # XXX consider making this "relation" or "object"
        self.filters = list()

    def add_filter(self, filter):
        self.filters.append(filter)

    def get_filter_exprs(self):
        return " and ".join([x.emit() for x in self.filters])

    def execute(self, cursor, values=None, columns=None, options=None):
        if columns is None:
            columns = self.table._columns

        text = self.emit(columns, options)

        if values is None:
            values = {}

        try:
            cursor.execute(text, values)
        except:
            log.debug("%s failed", self, exc_info=True)

            self.log_sql(cursor, text, values)

            raise

        if self.table._schema._model._model.sql_logging_enabled:
            self.log_sql(cursor, text, values)

    def emit(self, columns, options=None):
        raise Exception("Not implemented")

    def log_sql(self, cursor, text, values):
        log.debug("Sql text: %s", text)
        log.debug("Sql values:")

        for item in sorted(values.items()):
            log.debug("    %-34s  %r", *item)

        log.debug("Sql row count: %i", cursor.rowcount)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.table)

class SqlGetNewId(SqlOperation):
    def __init__(self, table, sequence):
        super(SqlGetNewId, self).__init__(table)

        self.sequence = sequence

    def emit(self, columns, options=None):
        return "select nextval('%s')" % self.sequence.identifier

class SqlSelect(SqlOperation):
    def emit(self, columns, options=None):
        tokens = list()

        cols = ", ".join([x.identifier for x in columns])
        table = getattr(self.table, "identifier", self.table)

        tokens.append("select %s from %s" % (cols, table))

        if self.filters:
            tokens.append("where %s" % self.get_filter_exprs())

        return " ".join(tokens)

class SqlSelectObject(SqlSelect):
    def __init__(self, table):
        super(SqlSelectObject, self).__init__(table)

        self.add_filter(SqlValueFilter(self.table._id))

class SqlSelectObjectByQmfId(SqlSelect):
    def __init__(self, table):
        super(SqlSelectObjectByQmfId, self).__init__(table)
        self.add_filter(SqlValueFilter(self.table._qmf_agent_id))
        self.add_filter(SqlValueFilter(self.table._qmf_object_id))

class SqlInsertObject(SqlOperation):
    def emit(self, columns, options=None):
        table = getattr(self.table, "identifier", self.table)
        names = [x.name for x in columns]
        cols = ", ".join(["\"%s\"" % x for x in names])
        vals = ", ".join(["%%(%s)s" % x for x in names])

        return "insert into %s (%s) values (%s)" % (table, cols, vals)

class SqlInsertObjectSamples(SqlOperation):
    def __init__(self, table):
        super(SqlInsertObjectSamples, self).__init__(table)

        self.extra_column_names = ()

    def emit(self, columns, options=None):
        table = getattr(self.table, "identifier", self.table)
        names = [x.name for x in columns]

        cols = ["\"%s\"" % x for x in names]
        vals = ["%%(%s)s" % x for x in names]

        for c in self.extra_column_names:
            cols.append("\"%s\"" % c)
            vals.append("%%(%s)s" % c)

        cols = ", ".join(cols)
        vals = ", ".join(vals)

        return "insert into %s (%s) values (%s)" % (table, cols, vals)
        
class SqlUpdate(SqlOperation):
    def emit(self, columns, options=None):
        tokens = list()

        table = getattr(self.table, "identifier", self.table)
        exprs = ["\"%s\" = %%(%s)s" % (x.name, x.name)
                 for x in columns
                 if x is not self.table.key_column]
        exprs = ", ".join(exprs)

        tokens.append("update %s set %s" % (table, exprs))

        if self.filters:
            tokens.append("where %s" % self.get_filter_exprs())

        return " ".join(tokens)

class SqlUpdateObject(SqlUpdate):
    def __init__(self, table):
        super(SqlUpdateObject, self).__init__(table)

        self.add_filter(SqlValueFilter(self.table._id))

class SqlDelete(SqlOperation):
    def emit(self, columns, options=None):
        tokens = list()

        table = getattr(self.table, "identifier", self.table)

        tokens.append("delete from %s" % table)

        if self.filters:
            tokens.append("where %s" % self.get_filter_exprs())

        return " ".join(tokens)

class SqlDeleteObject(SqlDelete):
    def __init__(self, table):
        super(SqlDeleteObject, self).__init__(table)

        self.add_filter(SqlValueFilter(self.table._id))

class SqlDeleteObjectSamples(SqlDelete):
    def __init__(self, table, time_col):
        super(SqlDeleteObjectSamples, self).__init__(table)

        that = "now() - interval '%(seconds)s seconds'"

        self.add_filter(SqlComparisonFilter(time_col, that, "<"))
