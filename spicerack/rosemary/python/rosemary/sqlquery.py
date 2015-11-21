from sqlmodel import *
from sqloperation import *
from util import *

log = logging.getLogger("rosemary.sqlquery")

class SqlQuery(SqlOperation):
    def __init__(self, table):
        super(SqlQuery, self).__init__(table)

        self.order_by = self.OrderBy()
        self.limit = self.Limit()
        self.group_by = self.GroupBy()

        self.joins = list()

    def emit(self, columns, options=None):
        tokens = list()

        cols = list()

        for column in columns:
            col = getattr(column, "identifier", column)
            if getattr(column, "alias", None):
                col = "%s as %s" % (col, column.alias)
            cols.append(col)

        tokens.append("select %s" % ", ".join(cols))

        table = getattr(self.table, "identifier", self.table)

        tokens.append("from %s" % table)

        for join in self.joins:
            tokens.append(join.emit())

        exprs = list()

        if self.filters:
            exprs.extend([x.emit() for x in self.filters])

        # XXX get rid of this
        if options and options.filters:
            exprs.extend([x.emit() for x in options.filters])

        if exprs:
            tokens.append("where %s" % " and ".join(exprs))

        if options:
            if options.group_column:
                tokens.append(self.group_by.emit(options.group_column,
                                                 options.group_having))

            if options.sort_column:
                tokens.append(self.order_by.emit(options.sort_column,
                                                 options.sort_ascending))

            tokens.append(self.limit.emit(options.limit, options.offset))

        return " ".join(tokens)

    class OrderBy(object):
        def emit(self, column, ascending):
            if ascending:
                direction = "asc"
            else:
                direction = "desc"

            alias = getattr(column, "alias", None)
            if not alias:
                alias = getattr(column, "identifier", column)

            return "order by %s %s" % (alias, direction)

    class Limit(object):
        def emit(self, limit, offset):
            if limit is None:
                limit = "all"

            return "limit %s offset %i" % (str(limit), offset)

    class GroupBy(object):
        def emit(self, column, filters):
            having = ""
            if filters:
                f_text = list()
                f_text.extend([x.emit() for x in filters])
                having = " having %s" % " and ".join(f_text)

            column = getattr(column, "identifier", column)
            return "group by %s%s" % (column, having)

class SqlQueryOptions(object):
    def __init__(self):
        self.group_column = None
        self.group_having = list()
        self.sort_column = None
        self.sort_ascending = True
        self.limit = None
        self.offset = 0
        self.filters = list()

class SqlQueryJoin(object):
    def __init__(self, query, table, this, that):
        assert query
        assert table
        assert this
        assert that

        self.query = query
        self.table = getattr(table, "identifier", table)
        self.this = getattr(this, "identifier", this)
        self.that = getattr(that, "identifier", that)

        assert self not in self.query.joins
        self.query.joins.append(self)

class SqlInnerJoin(SqlQueryJoin):
    def emit(self):
        args = (self.table, self.this, self.that)

        return "inner join %s on %s = %s" % args

class SqlOuterJoin(SqlQueryJoin):
    def emit(self):
        args = (self.table, self.this, self.that)

        return "left outer join %s on %s = %s" % args
