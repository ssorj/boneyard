import json
import os

from executor import Operation

class Director(object):
    def __init__(self):
        self.operations = list()

    def call_constructor(self, id, namespace, name, arguments=None):
        op = Operation("constructor-call")
        op.id = id
        op.namespace = namespace
        op.name = name
        op.arguments = arguments

        self.operations.append(op)

    def call_method(self, id, name, arguments=None):
        op = Operation("method-call")
        op.id = id
        op.name = name
        op.arguments = arguments

        self.operations.append(op)

    def marshal(self, output):
        for op in self.operations:
            output.write(op.marshal())
            output.write(os.linesep)
            output.flush()
