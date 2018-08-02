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

from __future__ import absolute_import
from __future__ import print_function

import logging as _logging
import os as _os
import proton as _proton
import re as _re
import sys as _sys
import time as _time
import urlparse as _urlparse

_log = _logging.getLogger("qpid_management")

class _Session(object):
    def __init__(self):
        self.debug = "QPID_MANAGEMENT_DEBUG" in _os.environ

        self._opened = False
        self._closed = False

        self._container = _proton.Container(self)

    def open(self):
        _log.debug("Opening %s", self)

        assert not self._opened
        assert not self._closed

        self._messenger.start()

        self._configure()

        self._opened = True

    def _configure(self):
        raise NotImplementedError()

    def process(self):
        args = self, self._messenger.incoming, self._messenger.outgoing
        _log.debug("Processing %s (%i incoming, %i outgoing)", *args)

        assert self._opened
        assert not self._closed

        try:
            self._messenger.recv(1)
        except _proton.Interrupt:
            pass

    def _send_message(self, message):
        _log.debug("Sending %s from %s", message, self)

        self._messenger.put(message)

    def _accept_message(self):
        if self._messenger.incoming == 0:
            return

        message = _proton.Message()

        self._messenger.get(message)
        self._messenger.accept()

        _log.debug("Accepting %s to %s", message, self)

        return message

    def close(self):
        _log.debug("Closing %s", self)

        assert self._opened
        assert not self._closed

        self._messenger.stop()

        self._closed = True

    def __enter__(self):
        self.open()
        
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        args = self.__class__.__name__, self._messenger.name[:8]
        return "{}({})".format(*args)

class ClientSession(_Session):
    def __init__(self):
        super(ClientSession, self).__init__()

        self.user = None
        self.password = None
        self.host = "localhost"
        self.port = "5672"

        self._current_request_id = 0
        self._requests_by_id = dict()

        self._dynamic_response_node_enabled = True
        self._response_address = None

    def check_connection(self):
        sock = _socket.socket()
        try:
            sock.connect((self.host, self.port))
        finally:
            sock.close()

    def _configure(self):
        auth = ""

        if self.user is not None:
            if self.password is not None:
                auth = "{}:{}@".format(self.user, self.password)
            else:
                auth = "{}@".format(self.user)

        server = "amqp://{}{}:{}/$1".format(auth, self.host, self.port)

        self._messenger.route("*", server)

        if self._dynamic_response_node_enabled:
            sub = self._messenger.subscribe("#")

            while sub.address is None:
                self._messenger.work()

            self._response_address = sub.address
        else:
            name = self._messenger.name
            address = "amqp://{}/responses".format(name)
            self._response_address = address

    def create_request(self):
        self._current_request_id += 1

        request_id = self._current_request_id
        request = Request(request_id, self._response_address)

        self._requests_by_id[request_id] = request

        return request

    def send_request(self, request):
        _log.debug("Sending %s from %s", request, self)

        request._check()

        message = request._marshal()
        message.reply_to = self._response_address

        self._send_message(message)

    def accept_response(self):
        message = self._accept_message()

        if message is None:
            return

        try:
            request = self._requests_by_id.pop(message.correlation_id)
        except KeyError:
            _log.info("Received response for an unknown request: %s", message)
            return

        response = Response._unmarshal(request, message)

        _log.debug("Accepting %s to %s", response, self)

        response._check()

        return response

class ServerSession(_Session):
    def __init__(self):
        super(ServerSession, self).__init__()

        self.host = "localhost"
        self.port = "5672"

    def _configure(self):
        self._messenger.subscribe("amqp://~{}:{}".format(self.host, self.port))

    def accept_request(self):
        message = self._accept_message()

        if message is None:
            return

        request = Request._unmarshal(message)

        _log.debug("Accepting %s to %s", request, self)

        return request

    def send_response(self, response):
        _log.debug("Sending %s from %s", response, self)

        message = response._marshal()

        self._send_message(message)

class Request(object):
    def __init__(self, id, response_address):
        assert id is not None
        assert response_address is not None

        self.id = id
        self.response_address = response_address

        self.address = None
        self.type = None
        self.operation = None
        self.locales = None

        self.name = None
        self.identity = None

        self.body = None

    def _check(self):
        assert self.address is not None
        assert self.type is not None
        assert self.name is not None or self.identity is not None

    def _marshal(self):
        assert self.operation is not None

        message = _proton.Message()

        message.correlation_id = self.id
        message.address = self.address

        message.properties = dict() # XXX PROTON-542
        message.properties["type"] = self.type
        message.properties["operation"] = self.operation

        if self.locales is not None:
            message.properties["locales"] = self.locales

        if self.name is not None:
            message.properties["name"] = self.name

        if self.identity is not None:
            message.properties["identity"] = self.identity

        if self.selected_type is not None:
            message.properties["entityType"] = self.selected_type

        message.body = self.body

        return message

    @classmethod
    def _unmarshal(cls, message):
        request = Request(message.correlation_id, message.reply_to)

        request.address = message.address

        props = message.properties

        request.type = props.get("type")
        request.operation = props["operation"]
        request.locales = props.get("locales")
        request.name = props.get("name")
        request.identity = props.get("identity")

        request.selected_type = props.get("entityType")

        request.body = message.body

        return request

    def respond(self, code, description, body=None):
        response = Response(self)

        response.status_code = code
        response.status_description = description

        response.body = body

        return response

    def respond_ok(self, body=None):
        return self.respond(200, "OK", body)

    def respond_created(self, body):
        return self.respond(201, "Created", body)

    def respond_no_content(self):
        return self.respond(204, "No Content")

    def respond_bad_request(self):
        return self.respond(400, "Bad Request")

    def respond_not_found(self):
        return self.respond(404, "Not Found")

    def respond_internal_server_error(self):
        return self.respond(500, "Internal Server Error")

    def respond_not_implemented(self):
        return self.respond(501, "Not Implemented")

    def __repr__(self):
        args = self.__class__.__name__, self.id, self.address, self.type, \
               self.operation, self.name
        return "{}({},{},{},{},{})".format(*args)

class Response(object):
    def __init__(self, request):
        self.request = request

        self.status_code = None
        self.status_description = None

        self.body = None

    def _marshal(self):
        assert self.status_code is not None

        message = _proton.Message()
        message.correlation_id = self.request.id
        message.address = self.request.response_address
        message.properties = dict() # XXX

        props = message.properties
        props["statusCode"] = self.status_code

        if self.status_description is not None:
            props["statusDescription"] = self.status_description

        message.body = self.body

        return message

    @classmethod
    def _unmarshal(cls, request, message):
        response = Response(request)
        props = message.properties

        response.status_code = props["statusCode"]
        response.status_description = props.get("statusDescription")
        response.body = message.body

        return response

    def _check(self):
        if self.status_code >= 200 and self.status_code < 300:
            return

        if self.status_code == 400:
            raise BadRequestError(self)

        if self.status_code == 404:
            raise NotFoundError(self)

        if self.status_code == 500:
            raise InternalServerError(self)

        if self.status_code == 501:
            raise NotImplementedError(self)

        msg = "Unexpected error with code {}: {}".format \
              (self.status_code, self.status_description)
        raise Exception(msg)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.status_code)

class RequestError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return self.response.status_description

class RequestTimeout(RequestError):
    pass

class BadRequestError(RequestError):
    pass
        
class NotFoundError(RequestError):
    pass

class InternalServerError(RequestError):
    pass

class NotImplementedError(RequestError):
    pass

class Node(object):
    def __init__(self, address):
        self.address = address

    def query(self, session, selected_type=None, attribute_names=None):
        type = "org.amqp.management"
        
        if attribute_names is None:
            attribute_names = ("type", "identity", "name")

        return self.call(session, type, "QUERY", name="self",
                         selected_type=selected_type,
                         attributeNames=attribute_names)

    def get_types(self, session, selected_type=None):
        type = "org.amqp.management"
        return self.call(session, type, "GET-TYPES", name="self",
                         selected_type=selected_type)

    def get_attributes(self, session, selected_type=None):
        type = "org.amqp.management"
        return self.call(session, type, "GET-ATTRIBUTES", name="self",
                         selected_type=selected_type)

    def get_operations(self, session, selected_type=None):
        type = "org.amqp.management"
        return self.call(session, type, "GET-OPERATIONS", name="self",
                         selected_type=selected_type)

    def get_other_nodes(self, session):
        type = "org.amqp.management"
        return self.call(session, type, "GET-MGMT-NODES", name="self")

    def create_entity(self, session, type, name, **attributes):
        assert type is not None
        assert name is not None
        assert "identity" not in attributes

        attributes["name"] = name

        attributes = self.call(session, type, "CREATE", **attributes)

        return Entity(self, attributes)

    def get_entity(self, session, type, identity):
        assert type is not None
        assert identity is not None

        attributes = dict()
        attributes["identity"] = identity

        attributes = self.call(session, type, "READ", **attributes)

        return Entity(self, attributes)

    def get_entity_by_name(self, session, type, name):
        assert type is not None
        assert name is not None

        request_attrs = dict()
        request_attrs["name"] = name

        response_attrs = self.call(session, type, "READ", **request_attrs)

        return Entity(self, response_attrs)

    def call(self, session, type, operation, **attributes):
        request = self.send_request(session, type, operation, **attributes)
        response = None

        while response is None:
            session.process()

            response = session.accept_response()

        assert response.request is request

        return response.body

    def send_request(self, session, type, operation, **attributes):
        request = session.create_request()

        request.address = self.address
        request.type = type
        request.operation = operation
        request.name = attributes.get("name")
        request.identity = attributes.get("identity")
        request.selected_type = attributes.get("selected_type")
        request.body = attributes

        session.send_request(request)

        return request

class Entity(object):
    def __init__(self, node, attributes):
        self.node = node
        self.attributes = attributes

    @property
    def type(self):
        return self.attributes["type"]

    @property
    def name(self):
        return self.attributes["name"]

    @property
    def identity(self):
        return self.attributes["identity"]

    def read(self, session):
        self.attributes = self.call(session, "READ")

    def update(self, session, **attributes):
        self.attributes = self.call(session, "UPDATE", **attributes)

    def delete(self, session):
        self.call(session, "DELETE")

    def call(self, session, operation, **attributes):
        attributes["identity"] = self.identity

        return self.node.call(session, self.type, operation, **attributes)
