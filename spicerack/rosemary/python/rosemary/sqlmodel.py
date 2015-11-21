from util import *

class SqlModel(object):
    def __init__(self, model):
        self._model = model

        self._schemas = list()
        self._schemas_by_name = dict()

    def write_create_ddl(self, out):
        for schema in self._schemas:
            schema.write_create_ddl(out)

        for schema in self._schemas:
            for table in schema._tables:
                table.write_alter_dll(out)

    def write_drop_ddl(self, out):
        for schema in self._schemas:
            schema.write_drop_ddl(out)

class SqlSchema(object):
    def __init__(self, model, name):
        self._model = model
        self._name = name

        self._model._schemas.append(self)
        self._model._schemas_by_name[self._name] = self

        mangled = self._name.replace(".", "_")

        if hasattr(self._model, mangled):
            raise Exception("Collision")

        setattr(self._model, mangled, self)

        # XXX _ this one too
        self.identifier = "\"%s\"" % self._name

        self._sequences = list()
        self._sequences_by_name = dict()

        self._tables = list()
        self._tables_by_name = dict()

        self._indexes = list()
        self._indexes_by_name = dict()

        self._views = list()
        self._views_by_name = dict()

    def write_create_ddl(self, out):
        out.write("create schema %s\n" % self.identifier)

        for seq in self._sequences:
            seq.write_create_ddl(out)

        for table in self._tables:
            table.write_create_ddl(out)

        for index in self._indexes:
            index.write_create_ddl(out)

        for view in self._views:
            view.write_create_ddl(out)

        out.write("    ;\n")

    def write_drop_ddl(self, out):
        out.write("drop schema %s cascade;\n" % self.identifier)

    def __repr__(self):
        args = (self.__class__.__name__, self._name)
        return "%s(%s)" % args

class SqlSequence(object):
    def __init__(self, schema, name):
        assert isinstance(schema, SqlSchema)

        self.schema = schema
        self.name = name

        self.identifier = "%s.\"%s\"" % (self.schema.identifier, self.name)

        self.schema._sequences.append(self)
        self.schema._sequences_by_name[self.name] = self

    def write_create_ddl(self, out):
        out.write("    create sequence \"%s\"\n" % self.name)

class SqlTable(object):
    def __init__(self, schema, name):
        assert isinstance(schema, SqlSchema)

        self._schema = schema
        self._name = name

        self._schema._tables.append(self)
        self._schema._tables_by_name[self._name] = self

        if hasattr(self._schema, self._name):
            raise Exception("Collision")

        setattr(self._schema, self._name, self)

        # XXX _ these as well
        self.identifier = "%s.\"%s\"" % (self._schema.identifier, self._name)
        self.key_column = None

        self._columns = list()
        self._columns_by_name = dict()

        self._constraints = list()
        self._deferred_constraints = list()

    def write_create_ddl(self, out):
        out.write("    create table \"%s\" (" % self._name)

        exprs = list()

        for col in self._columns:
            exprs.append(col.get_ddl())

        for constraint in self._constraints:
            exprs.append(constraint.get_ddl())

        exprs = ["\n        %s" % x.strip() for x in exprs]

        out.write(",".join(exprs))

        out.write("\n        )\n")

    def write_alter_dll(self, out):
        if not self._deferred_constraints:
            return

        out.write("alter table %s\n    " % self.identifier)

        constraints = [x.get_ddl() for x in self._deferred_constraints]

        out.write(",\n    ".join(constraints))

        out.write("\n    ;\n")

    def __repr__(self):
        args = (self.__class__.__name__, self._schema._name, self._name)
        return "%s(%s,%s)" % args

class SqlColumn(object):
    def __init__(self, table, name, type):
        self.table = table
        self.name = name
        self.type = type
        self.alias = None

        self.table._columns.append(self)
        self.table._columns_by_name[self.name] = self

        if hasattr(self.table, self.name):
            raise Exception("%s already has %s" % (self.table, self.name))

        setattr(self.table, self.name, self)

        self.identifier = "\"%s\".\"%s\"" % (self.table._name, self.name)

        self.nullable = False
        self.foreign_key_column = None

    def get_ddl(self):
        tokens = list()

        tokens.append("\"%s\"" % self.name)
        tokens.append(self.type.literal)

        if not self.nullable:
            tokens.append("not null")

        return " ".join(tokens)

    def __repr__(self):
        args = (self.__class__.__name__, self.table._name, self.name)
        return "%s(%s,%s)" % args

class SqlTableConstraint(object):
    def __init__(self, table, name, columns):
        self.table = table
        self.name = name
        self.columns = columns

        self.table._constraints.append(self)

class SqlPrimaryKeyConstraint(SqlTableConstraint):
    def get_ddl(self):
        cols = ", ".join(["\"%s\"" % x.name for x in self.columns])

        return "constraint \"%s\" primary key (%s)" % (self.name, cols)

class SqlUniqueConstraint(SqlTableConstraint):
    def get_ddl(self):
        cols = "\"%s\"" % "\", \"".join([x.name for x in self.columns])

        return "constraint \"%s\" unique (%s)" % (self.name, cols)

class SqlForeignKeyConstraint(object):
    def __init__(self, table, name, this_column, that_column):
        self.table = table
        self.name = name
        self.this_column = this_column
        self.that_column = that_column

        self.table._deferred_constraints.append(self)

        self.on_update = "cascade"
        self.on_delete = "set null"

    def get_ddl(self):
        tokens = list()

        tokens.append("add constraint \"%s\"" % self.name)
        tokens.append("foreign key (\"%s\")" % self.this_column.name)
        tokens.append("references %s" % self.that_column.table.identifier)
        tokens.append("(\"%s\")" % self.that_column.name)
        tokens.append("on update %s" % self.on_update)
        tokens.append("on delete %s" % self.on_delete)
        
        return " ".join(tokens)

class SqlIndex(object):
    def __init__(self, schema, name, columns):
        assert len(set([x.table for x in columns])) == 1

        self.schema = schema
        self.name = name
        self.columns = columns

        self.schema._indexes.append(self)
        self.schema._indexes_by_name[self.name] = self

    def write_create_ddl(self, out):
        cols = ", ".join(["\"%s\"" % x.name for x in self.columns])
        args = (self.name, self.columns[0].table._name, cols)

        out.write("    create index \"%s\" on \"%s\" (%s)\n" % args)

class SqlView(object):
    def __init__(self, schema, name, query):
        self.schema = schema
        self.name = name
        self.query = query

        self.schema._views.append(self)
        self.schema._views_by_name[self.name] = self

        self.identifier = "%s.\"%s\"" % (self.schema.identifier, self.name)

    def write_create_ddl(self, out):
        query = self.query.emit(("*",))

        out.write("    create view \"%s\" as %s" % (self.name, query))
