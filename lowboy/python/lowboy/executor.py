import json
import os

class Executor(object):
    def __init__(self):
        self.operations = list()
        self.variables = dict()

    def unmarshal(self, input):
        for line in input.readlines():
            op = Operation(None)
            op.unmarshal(line)

            self.operations.append(op)

    def execute(self):
        for op in self.operations:
            op.execute(self.variables)

class Operation(object):
    def __init__(self, type):
        self.type = type
        self.id = None
        self.namespace = None
        self.name = None
        self.arguments = None

    def marshal(self):
        data = {
            "type": self.type,
            "id": self.id,
            "namespace": self.namespace,
            "name": self.name,
            "arguments": self.arguments,
            }

        return json.dumps(data)

    def unmarshal(self, string):
        data = json.loads(string)

        self.type = data["type"]
        self.id = data["id"]
        self.namespace = data["namespace"]
        self.name = data["name"]
        self.arguments = data["arguments"]

    def execute(self, variables):
        if self.type == "method-call":
            obj = variables[id]
            meth = getattr(obj, self.name)

            meth() # XXX args
        elif self.type == "constructor-call":
            mod = __import__(self.namespace)
            cls = getattr(mod, self.name)
            obj = cls() # XXX args

            variables[id] = obj
