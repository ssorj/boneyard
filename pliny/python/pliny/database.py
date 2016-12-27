#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from common import *

from cabinet.account import *
from sqlalchemy import Column as _Column
from sqlalchemy import DateTime as _DateTime
from sqlalchemy import ForeignKey as _ForeignKey
from sqlalchemy import Integer as _Integer
from sqlalchemy import String as _String
from sqlalchemy import create_engine as _create_engine
from sqlalchemy.ext.declarative import declarative_base as _declarative_base
from sqlalchemy.ext.declarative import declared_attr as _declared_attr
from sqlalchemy.orm import relationship as _relationship
from sqlalchemy.orm import sessionmaker as _sessionmaker
from sqlalchemy.orm.session import Session as _Session
from threading import local as _local

_log = logger("pliny.database")

_thread_local_data = _local()

class Database(object):
    def __init__(self, app, file):
        self.app = app
        self.file = file

        self.engine = None

    def init(self):
        _log.info("Initializing %s", self)

        uri = "sqlite:///%s" % self.file
        self.engine = _create_engine(uri, echo=self.app.debug)

        _DatabaseObject.metadata.create_all(self.engine)
        DatabaseSession.configure(bind=self.engine)

    def get_session(self):
        if not hasattr(_thread_local_data, "session"):
            _thread_local_data.session = DatabaseSession()

        return _thread_local_data.session

    def __repr__(self):
        args = self.__class__.__name__, self.file
        return "%s(%s)" % args

class DatabaseSession(_Session):
    def get_user(self, name):
        return self.query(User).filter(User.name == name).first()

    def get_user_by_email(self, email):
        return self.query(User).filter(User.email == email).first()

    def get_queue(self, name):
        return self.query(Queue).filter(Queue.name == name).first()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

class _DatabaseObject(object):
    id = _Column(_Integer, primary_key=True)

    @_declared_attr
    def __tablename__(cls):
        return cls.__name__

    def __repr__(self):
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args

DatabaseSession = _sessionmaker(class_=DatabaseSession)
_DatabaseObject = _declarative_base(cls=_DatabaseObject)

class User(_DatabaseObject):
    name = _Column(_String, nullable=False, unique=True)
    email = _Column(_String, nullable=False, unique=True)
    last_login = _Column(_DateTime)
    last_logout = _Column(_DateTime)
    queues = _relationship("Queue", collection_class=set, backref="user")

class Queue(_DatabaseObject):
    user_id = _Column(_Integer, _ForeignKey("User.id"))

    name = _Column(_String, nullable=False, unique=True)
    access = _Column(_String, nullable=False, default="private")
    distribution_mode = _Column(_String, nullable=False, default="single")
    status = _Column(_String, nullable=False, default="unprovisioned")

class Account(AccountAdapter):
    def __init__(self, user):
        super(Account, self).__init__()

        _log.debug("Creating account adapter for %s", user)

        self._user = user

    @property
    def user(self):
        return self._user

    @property
    def name(self):
        return self.user.name

    @property
    def email(self):
        return self.user.email

    @property
    def last_login(self):
        return self.user.last_login

    @property
    def last_logout(self):
        return self.user.last_logout

class AccountDatabase(AccountDatabaseAdapter):
    def __init__(self, app):
        self.app = app

    def login(self, session, name, password):
        user = session.database.get_user(name)

        if user is None:
            raise BadCredentialsError()

        with session.database:
            user.last_login = datetime.now()

        return Account(user)

    def logout(self, session, account):
        account.user.last_logout = datetime.now()

    def create(self, session, name, email, password):
        existing_name = session.database.get_user(name)
        existing_email = session.database.get_user_by_email(email)

        if existing_name or existing_email:
            raise AccountAlreadyExistsError()

        with session.database:
            user = User()
            user.name = name
            user.email = email
            user.last_login = datetime.now()
            # XXX password!

            session.database.add(user)

        return Account(user)

    def change_email(self, session, account, email, password, new_email):
        if email != account.email:
            raise BadCredentialsError()

        # XXX password!

        with session.database:
            account.user.email = new_email

    def change_password(self, session, account, email, password, new_password):
        if email != account.email:
            raise BadCredentialsError()

        # XXX password!

        with session.database:
            account.user.password = new_password
