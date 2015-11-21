from rosemary.sqlquery import *
from wooly.datatable import *

from util import *

class SqlAdapter(DataAdapter):
    def __init__(self, app, table):
        super(SqlAdapter, self).__init__()

        self.app = app
        self.table = table

        self.query = SqlQuery(self.table)
        self.columns = list()

    def get_count(self, values):
        # XXX urgh.  I want session in here

        cursor = self.app.database.get_read_cursor()

        self.query.execute(cursor, values, columns=("count(1)",))

        return cursor.fetchone()[0]

    def get_sql_options(self, options):
        sql_options = SqlQueryOptions()

        if options.sort_field:
            sql_options.sort_column = options.sort_field.column

        sql_options.sort_ascending = options.sort_ascending
        sql_options.limit = options.limit
        sql_options.offset = options.offset

        return sql_options

    def get_data(self, values, options):
        sql_options = self.get_sql_options(options)

        cursor = self.app.database.get_read_cursor()

        self.query.execute(cursor, values,
                           columns=self.columns,
                           options=sql_options)

        return cursor.fetchall()

class SqlField(DataAdapterField):
    def __init__(self, adapter, column):
        python_type = column.type.python_type

        super(SqlField, self).__init__(adapter, column.name, python_type)

        self.column = column

        self.adapter.columns.append(column)

class ObjectSqlAdapter(SqlAdapter):
    def __init__(self, app, cls):
        super(ObjectSqlAdapter, self).__init__(app, cls.sql_table)

        self.cls = cls

        self.fields_by_attr = dict()

        self.id_field = self.get_id_field(cls)

    def get_id_field(self, cls):
        return ObjectSqlField(self, self.cls._id)

    def add_join(self, cls, this, that):
        assert cls
        assert this
        assert that

        SqlInnerJoin(self.query, cls.sql_table,
                     this.sql_column, that.sql_column)

    def add_outer_join(self, cls, this, that):
        assert cls
        assert this
        assert that

        SqlOuterJoin(self.query, cls.sql_table,
                     this.sql_column, that.sql_column)

    def add_value_filter(self, attr):
        assert attr
        value = "%%(%s)s" % attr.name

        filter = SqlComparisonFilter(attr.sql_column, value)
        self.query.add_filter(filter)

    def add_like_filter(self, attr):
        assert attr

        filter = SqlLikeFilter(attr.sql_column)
        self.query.add_filter(filter)

class ObjectSqlField(SqlField):
    def __init__(self, adapter, attr):
        assert isinstance(adapter, ObjectSqlAdapter), adapter

        super(ObjectSqlField, self).__init__(adapter, attr.sql_column)

        self.attr = attr

        self.adapter.fields_by_attr[self.attr] = self

    def get_title(self, session):
        return self.attr.title or self.attr.name

class HeartbeatField(SqlField):
    def get_title(self, session):
        return "Status"

    def get_content(self, session, record):
        id = record[self.index]

        try:
            last = self.adapter.app.model.mint.model.agents[id].last_heartbeat
        except KeyError:
            last = None

        if last is None:
            return "Unknown"

        if last < datetime.now() - timedelta(seconds=10):
            return "Stale"

        return "Fresh"

class TestData(ObjectSqlAdapter):
    def __init__(self, app):
        broker = app.model.org_apache_qpid_broker.Broker
        system = app.model.org_apache_qpid_broker.System
        cluster = app.model.org_apache_qpid_cluster.Cluster

        super(TestData, self).__init__(app, broker)

        self.add_join(system, broker.systemRef, system.id)
        self.add_outer_join(cluster, broker.id, cluster.brokerRef)

        col = self.table._qmf_agent_id
        field = HeartbeatField(self, col)

        for prop in broker._properties + system._properties:
            field = ObjectSqlField(self, prop)
