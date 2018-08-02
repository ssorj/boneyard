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

from __future__ import print_function

import inspect
import os
import sys
import time
import traceback

from collections import defaultdict
from threading import Lock, Thread
from traceback import print_exc
from uuid import uuid4

from qpid_management import *

class TestClient(object):
    def __init__(self):
        self.collections = list()

        SelfNodeTest(self)
        QueryTest(self)
        EntityTest(self)

        self.debug = "QPID_MANAGEMENT_DEBUG" in os.environ

    def run(self, session):
        total = 0
        passed = 0
        failed = 0
        skipped = 0

        for collection in self.collections:
            collection.setup(session)
            collection.run(session)
            collection.teardown(session)

            total += collection.total
            passed += collection.passed
            failed += collection.failed
            skipped += collection.skipped

        verb = "was" if skipped == 1 else "were"
        args = total, passed, failed, skipped, verb
        msg = "Result: Of {} tests, {} passed, {} failed, and {} {} skipped"

        print(msg.format(*args))

class TestCollection(object):
    def __init__(self, client):
        self.client = client

        self.node = Node("$management")

        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0

        self.client.collections.append(self)

    def setup(self, session):
        pass

    def teardown(self, session):
        pass

    def run(self, session):
        for name, meth in inspect.getmembers(self, inspect.ismethod):
            if not name.startswith("test"):
                continue

            qualified_name = "{}.{}".format(self.__class__.__name__, name)

            sys.stdout.write("{:70}  ".format(qualified_name))
            sys.stdout.flush()

            self.total += 1

            try:
                meth(session)

                print("Passed")
                self.passed += 1
            except KeyboardInterrupt:
                raise
            except SkippedTest:
                print("Skipped")
                self.skipped += 1
            except Exception, e:
                print("Failed ***")
                self.failed += 1
                traceback.print_exc()
            finally:
                sys.stdout.flush()

            assert self.passed + self.failed + self.skipped == self.total

    def check_result(self, result, type_):
        msg = "Unexpected null result"
        assert result is not None, msg

        msg = "Expected result to be of type '{}' but found '{}'"
        msg = msg.format(type_.__name__, type(result))
        assert isinstance(result, type_), msg

class SkippedTest(Exception):
    pass

class SelfNodeTest(TestCollection):
    def test_read(self, session):
        type = "org.amqp.management"
        entity = self.node.get_entity_by_name(session, type, "self")

        msg = "Expected type 'org.amqp.management' but found '{}'".format \
              (entity.type)
        assert entity.type == "org.amqp.management", msg

        msg = "Expected name 'self' but found '{}'".format(entity.name)
        assert entity.name == "self", msg

    def test_get_types(self, session):
        types = self.node.get_types(session)

        self.check_result(types, dict)

        msg = "Expected type 'org.amqp.management' not found in {}"
        msg = msg.format(types.keys())
        assert "org.amqp.management" in types, msg

    def test_get_types_filtered(self, session):
        types = self.node.get_types(session, "org.amqp.management")

        self.check_result(types, dict)
        
        # "Expected only one type in the result; found {}"

        msg = "Expected type 'org.amqp.management' not found in {}"
        msg = msg.format(types.keys())
        assert "org.amqp.management" in types, msg

    def test_get_attributes(self, session):
        attributes = self.node.get_attributes(session)

        self.check_result(attributes, dict)

    def test_get_attributes_filtered(self, session):
        attributes = self.node.get_attributes(session, "org.amqp.management")

        self.check_result(attributes, dict)

        msg = "Expected only one type in the result; found {}"
        msg = msg.format(len(attributes))
        assert len(attributes) == 1, msg

        msg = "Expected type 'org.amqp.management' not found in {}"
        msg = msg.format(attributes.keys())
        assert "org.amqp.management" in attributes, msg

    def test_get_operations(self, session):
        operations = self.node.get_operations(session)

        self.check_result(operations, dict)

    def test_get_operations_filtered(self, session):
        operations = self.node.get_operations(session, "org.amqp.management")

        self.check_result(operations, dict)

        # "Expected only one type in the result; found {}"

        msg = "Expected type 'org.amqp.management' not found in {}"
        msg = msg.format(operations.keys())
        assert "org.amqp.management" in operations, msg

    def test_get_other_nodes(self, session):
        nodes = self.node.get_other_nodes(session)

        self.check_result(nodes, list)

    def xxx_test_register(self, session):
        pass

    def xxx_test_deregister(self, session):
        pass

class QueryTest(TestCollection):
    def test_query_all(self, session):
        results = self.node.query(session)

        self.check_result(results, dict)

class EntityTest(TestCollection):
    def setup(self, session):
        type = "com.example.broker.queue" # XXX need a type I can manipulate

        namespace = str(uuid4())[:4]
        entity_name = "{}/entity1".format(namespace)
        delete_name = "{}/delete1".format(namespace)

        self.entity = self.node.create_entity(session, type, entity_name)
        self.delete_target = self.node.create_entity(session, type, delete_name)

    def xxx_test_create(self, session):
        pass

    def test_read(self, session):
        self.entity.read(session)

    def test_update(self, session):
        new_name = self.entity.name + "_updated"

        self.entity.update(session, name=new_name)

        msg = "Update to name attribute had no effect"
        assert self.entity.name == new_name, msg

    def test_delete(self, session):
        self.delete_target.delete(session)

class TestServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.debug = False

        self.model = TestModel()

        self._stop_requested = False

    def log(self, message, *args):
        if not self.debug:
            return
        
        message = message.format(*args)

        print("Server: {}".format(message))

    def run(self):
        self.log("Starting")

        session = ServerSession()
        session.host = self.host
        session.port = self.port
        session.debug = self.debug

        with session:
            self.log("Listening on port {}", session.port)

            while True:
                if self._stop_requested:
                    self.log("Stopping")
                    break

                try:
                    self.tick(session)
                except KeyboardInterrupt:
                    raise
                except:
                    print_exc()
                    time.sleep(1)

    def stop(self):
        self._stop_requested = True

    def tick(self, session):
        session.process()

        request = session.accept_request()

        if request is None:
            return

        self.log("Received {}", request)

        response = self.process_request(request)

        self.log("Sending {}", response)

        session.send_response(response)

    def process_request(self, request):
        if None in (request.address, request.type, request.operation):
            return request.respond_bad_request()

        try:
            node = self.model.nodes_by_address[request.address]
        except KeyError:
            return request.respond_not_found() # XXX not clear this is correct

        try:
            type = node.types_by_name[request.type]
        except KeyError:
            return request.respond_not_found() # XXX not clear this is correct

        try:
            operation = type.operations_by_name[request.operation]
        except KeyError:
            return request.respond_not_implemented()

        try:
            with self.model.lock:
                return operation(request)
        except KeyboardInterrupt:
            raise
        except:
            print_exc()
            return request.respond_internal_server_error()

class _Model(object):
    def __init__(self):
        self.nodes_by_address = dict()
        self.lock = Lock()

class _Node(object):
    def __init__(self, model, address):
        self.model = model
        self.address = address

        self.entities_by_name = dict()
        self.entities_by_identity = dict()
        self.entities_by_type = defaultdict(set)

        self.types_by_name = dict()

        assert self.address not in self.model.nodes_by_address
        self.model.nodes_by_address[self.address] = self

    def get_entity(self, request):
        if request.identity is not None:
            try:
                return self.entities_by_identity[request.identity]
            except KeyError:
                pass

        if request.name is not None:
            try:
                return self.entities_by_name[request.name]
            except KeyError:
                pass

class _Entity(object):
    def __init__(self, node, name, type):
        self.model = node.model
        self.node = node
        self.type = type
        self.identity = str(uuid4())

        self._name = None
        self.name = name

        self.node.entities_by_identity[self.identity] = self
        self.node.entities_by_type[self.type].add(self)

    def delete(self):
        del self.node.entities_by_name[self.name]
        del self.node.entities_by_identity[self.identity]
        self.node.entities_by_type[self.type].remove(self)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name == self.name:
            return

        assert name not in self.node.entities_by_name, name

        prev_name = self.name
        self._name = name

        if prev_name is not None:
            self.node.entities_by_name.pop(prev_name)

        self.node.entities_by_name[self._name] = self

    def get_attributes(self):
        attributes = dict()

        for name in self.type.attribute_names:
            if name == "type":
                attributes[name] = self.type.name
                continue

            attributes[name] = getattr(self, name)

        return attributes

    def set_attributes(self, request):
        for name in self.type.attribute_names:
            if name in ("type", "identity"):
                continue

            try:
                value = request.body[name]
            except KeyError:
                continue

            setattr(self, name, value)

        return self.get_attributes()

class _Type(object):
    def __init__(self, node, name, supertypes=()):
        self.model = node.model
        self.node = node
        self.name = name
        self.supertypes = supertypes

        self.attribute_names = set()
        self.attribute_names.add("name")
        self.attribute_names.add("type")
        self.attribute_names.add("identity")

        self.operations_by_name = dict()
        self.operations_by_name["CREATE"] = self.create
        self.operations_by_name["READ"] = self.read
        self.operations_by_name["UPDATE"] = self.update
        self.operations_by_name["DELETE"] = self.delete

        assert self.name not in self.node.types_by_name
        self.node.types_by_name[self.name] = self

    def create(self, request):
        if request.body:
            for name in request.body:
                if name not in self.attribute_names:
                    return request.respond_bad_request()

        entity = _Entity(self.node, request.name, self)
        attributes = entity.set_attributes(request)

        return request.respond_created(attributes)

    def read(self, request):
        entity = self.node.get_entity(request)

        if entity is None:
            return request.respond_not_found()

        attributes = entity.get_attributes()

        return request.respond_ok(attributes)

    def update(self, request):
        entity = self.node.get_entity(request)

        if entity is None:
            return request.respond_not_found()

        attributes = entity.set_attributes(request)

        return request.respond_ok(attributes)

    def delete(self, request):
        entity = self.node.get_entity(request)

        if entity is None:
            return request.respond_not_found()

        entity.delete()

        return request.respond_no_content()

class _SelfType(_Type):
    def __init__(self, node):
        super(_SelfType, self).__init__(node, "org.amqp.management")

        self.operations_by_name["QUERY"] = self.query
        self.operations_by_name["GET-TYPES"] = self.get_types
        self.operations_by_name["GET-ATTRIBUTES"] = self.get_attributes
        self.operations_by_name["GET-OPERATIONS"] = self.get_operations
        self.operations_by_name["GET-MGMT-NODES"] = self.get_mgmt_nodes

    def query(self, request):
        names = "type", "identity", "name"
        results = list()

        for name in sorted(self.node.entities_by_name):
            entity = self.node.entities_by_name[name]
            results.append((entity.type.name, entity.identity, entity.name))

        body = {"attributeNames": names, "results": results}

        return request.respond_ok(body)

    def get_types(self, request):
        types = dict()

        for name, type in self.node.types_by_name.items():
            types[name] = [x.name for x in sorted(type.supertypes)]

        return request.respond_ok(types)

    def get_attributes(self, request):
        types = dict()

        selected = request.selected_type

        if selected is None:
            for name, type in self.node.types_by_name.items():
                types[name] = sorted(type.attribute_names)
        elif selected in self.node.types_by_name:
            type = self.node.types_by_name[selected]
            types[type.name] = sorted(type.attribute_names)

        return request.respond_ok(types)

    def get_operations(self, request):
        types = dict()

        for name, type in self.node.types_by_name.items():
            types[name] = sorted(type.operations_by_name)

        return request.respond_ok(types)

    def get_mgmt_nodes(self, request):
        nodes = [a for a, n in self.model.nodes_by_address.items()
                 if n is not self.node]

        return request.respond_ok(sorted(nodes))

class TestModel(_Model):
    def __init__(self):
        super(TestModel, self).__init__()

        with self.lock:
            node = _Node(self, "$management")
            
            self_type = _SelfType(node)
            test_type = _Type(node, "com.example.broker.queue")

            _Entity(node, "self", self_type)
            _Entity(node, "arnold", test_type)

            other_node = _Node(self, "other-node")

            _Entity(other_node, "self", self_type)

class TestServerThread(Thread):
    def __init__(self, host, port):
        super(TestServerThread, self).__init__()

        self.server = TestServer(host, port)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.stop()
