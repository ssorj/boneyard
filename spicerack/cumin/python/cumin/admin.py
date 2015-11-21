from StringIO import StringIO

from util import *
from rosemary.sqlquery import SqlQuery, SqlInnerJoin
from rosemary.sqlfilter import SqlComparisonFilter
from psycopg2 import IntegrityError, ProgrammingError

log = logging.getLogger("cumin.admin")

schema_version = "1.3a"

class SchemaMissing(Exception):
    pass

class SchemaVersion(Exception):
    pass

class CuminAdmin(object):
    def __init__(self, app):
        self.app = app

    def get_schema(self):
        writer = StringIO()
        self.app.model.sql_model.write_create_ddl(writer)
        return writer.getvalue()

    def create_schema(self, cursor):
        
        # Check for meta scripts in the upgrade
        # dir associated with the schema version.
        # This lets us associate external tasks
        # with schema version numbers.
        upgrade_dir = os.path.join(self.app.home, "model/upgrades")
        try:
            target = None
            scripts = os.listdir(upgrade_dir)
            for s in scripts:
                if s == "create_%s" % schema_version:
                    target = os.path.join(upgrade_dir, s)
                    break
        except:
            # nothing, we assume
            pass
        
        conn = None
        if target:
            res = subprocess.Popen(target, shell=True).wait()
            if res != 0:
                print "Executed script %s" % target
                print "Script exited with error code %s" % res
                raise Exception("Schema not created")
            else:
                # Well, some scripts might restart the server
                # Get the connection back.  Try multiple, the server
                # may be in the process of starting
                for i in range(20):
                    try:
                        conn = self.app.database.get_connection()
                        break
                    except:
                        import time
                        time.sleep(0.5)
                if conn is None:
                    print "Can't connect to the database."
                    raise Exception("Schema not created")
                cursor = conn.cursor()

        cursor.execute(self.get_schema())

        cls = self.app.model.com_redhat_cumin.Info

        obj = cls.create_object(cursor)
        obj.schema_version = schema_version
        obj.fake_qmf_values()
        obj.save(cursor)
        return conn, cursor

    def update_schema_version(self, cursor, version):
        cls = self.app.model.com_redhat_cumin.Info
        info = cls.get_object(cursor)
        info.schema_version = version
        info.save(cursor)

    def get_schema_version(self, cursor):
        cls = self.app.model.com_redhat_cumin.Info
        try:
            info = cls.get_object(cursor)
        except ProgrammingError:
            info = None

        if not info:
            raise SchemaMissing("The schema isn't there")
        return info.schema_version
        
    def get_target_schema_version(self):
        return schema_version

    def check_schema(self, cursor):
        cls = self.app.model.com_redhat_cumin.Info
        try:
            info = cls.get_object(cursor)
        except ProgrammingError:
            info = None

        if not info:
            raise SchemaMissing("The schema isn't there")

        if info.schema_version != schema_version:
            args = (schema_version, info.schema_version)
            msg = "Expected schema version %s, found version %s" % args
            raise SchemaVersion(msg)

        return info.schema_version

    def drop_schema(self, cursor):
        cls = self.app.model.com_redhat_cumin.Info
        try:
            info = cls.get_object(cursor)
        except ProgrammingError:
            raise SchemaMissing("The schema isn't there")

        writer = StringIO()
        self.app.model.sql_model.write_drop_ddl(writer)
        sql = writer.getvalue()

        cursor.execute(sql)

    def get_role(self, cursor, name):
        cls = self.app.model.com_redhat_cumin.Role
        return cls.get_object(cursor, name=name)

    def add_role(self, cursor, name):
        cls = self.app.model.com_redhat_cumin.Role

        role = cls.create_object(cursor)
        role.name = name
        role.fake_qmf_values()
        role.save(cursor)

        return role

    def get_user(self, cursor, name):
        cls = self.app.model.com_redhat_cumin.User
        return cls.get_object(cursor, name=name)

    def add_user(self, cursor, name, crypted_password):
        cls = self.app.model.com_redhat_cumin.User

        # Check for existence of the user first.
        # This will save exception traces and sql
        # dumps in the log file.
        if cls.get_object(cursor, name=name):
            raise IntegrityError("Duplicate cumin user")

        user = cls.create_object(cursor)
        user.name = name
        user.password = crypted_password
        user.fake_qmf_values()
        user.save(cursor)

        return user

    def get_assignment(self, cursor, user, role):
        cls = self.app.model.com_redhat_cumin.UserRoleMapping

        mapping = cls.get_object(cursor, _user_id=user._id, _role_id=role._id)

        return mapping

    def add_assignment(self, cursor, user, role):
        cls = self.app.model.com_redhat_cumin.UserRoleMapping

        mapping = cls.create_object(cursor)
        mapping._user_id = user._id
        mapping._role_id = role._id
        mapping.fake_qmf_values()
        mapping.save(cursor)

        return mapping

    def get_roles_for_user(self, cursor, user):
        user_cls = self.app.model.com_redhat_cumin.User
        role_cls = self.app.model.com_redhat_cumin.Role
        mapping_cls = self.app.model.com_redhat_cumin.UserRoleMapping

        query = SqlQuery(role_cls.sql_table)

        SqlInnerJoin(query,
            mapping_cls.sql_table,
            mapping_cls.role.sql_column,
            role_cls._id.sql_column)

        SqlInnerJoin(query,
            user_cls.sql_table,
            user_cls._id.sql_column,
            mapping_cls.user.sql_column)
        #TODO: one column ? 
        cols = [ role_cls.name.sql_column ]
        filt = SqlComparisonFilter(user_cls._id.sql_column, user._id, 
                             gen_cursor = self.app.database.get_read_cursor)
        query.add_filter(filt)
        sql = query.emit(cols)
        cursor.execute(sql)
        return [x[0] for x in cursor.fetchall()]
