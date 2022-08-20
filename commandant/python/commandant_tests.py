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

from commandant import *

def test_command(session):
    command = Command()
    command.main(["--init-only"])

    command = Command()

    try:
        command.main([])
    except NotImplementedError:
        pass

    class ExampleCommand(Command):
        def __init__(self):
            super(ExampleCommand, self).__init__(name="example")

            self.description = "alpha"
            self.epilog = "beta"

        def main(self, args=None):
            print("Hello")
            print(self.description)
            print(self.epilog)

    command = ExampleCommand()
    command.main([])

    command.main(["--help"])

def test_logging(session):
    raise TestSkipped("Not yet implemented")

def test_test_command(session):
    command = TestCommand()
    command.main(["--init-only"])

    command = TestCommand()
    command.main(["--list"])

    command = TestCommand()

    try:
        command.main([])
    except SystemExit:
        pass
