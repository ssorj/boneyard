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

from model import *
from html import *
from python import *
from java import *
from c import *

class Pumpjack(object):
    def __init__(self, input_dir):
        self.input_dir = input_dir

        self.model = None

    def load(self):
        input_path = os.path.join(self.input_dir, "module.xml")
        tree = ElementTree()

        try:
            file = open(input_path)
        except IOError:
            msg = "Cannot open input path '%s'" % input_path
            raise PumpjackException(msg)

        try:
            tree.parse(file)
        finally:
            file.close()

        elem = tree.getroot()

        self.model = PumpjackModel(elem)
        self.model.process()

    def render(self, output_dir, renderer_name):
        assert self.model is not None

        try:
            renderer_class = renderer_classes_by_name[renderer_name]
        except KeyError:
            msg = "Renderer '%s' is unknown" % renderer_name
            raise PumpjackException(msg)

        renderer = renderer_class(output_dir)

        try:
            renderer.render(self.model)
        except IOError, e:
            msg = "Cannot render: %s" % str(e)
            raise PumpjackException(msg)

class PumpjackException(Exception):
    pass
