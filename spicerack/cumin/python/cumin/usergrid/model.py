from wooly.sql import *

strings = StringCatalog(__file__)

class Object(object):
    pass

class UserSqlOperation(SqlOperation):
    def __init__(self, app, user):
        super(UserSqlOperation, self).__init__(app)

        self.user = user

    def render_user_name(self, session):
        return self.user.get(session).name

    def get_connection(self, session):
        return self.app.database.get_read_connection()

    def get_object(self, session):
        cursor = self.execute(session)

        record = cursor.fetchone()
        description = cursor.description

        obj = Object()

        for value, metadata in zip(record, description):
            setattr(obj, metadata[0], value)

        return obj

class LoadUserJobStats(UserSqlOperation):
    pass

class LoadUserSlotStats(UserSqlOperation):
    pass
