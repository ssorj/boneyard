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

import argparse as _argparse

from qpid_management import *
from spindle import *

class ToolArgumentParser(_argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = _ToolHelpFormatter

        super(ToolArgumentParser, self).__init__(*args, **kwargs)
        
        self.add_argument("--user", metavar="USER",
                          help="connect as USER")
        self.add_argument("--password", metavar="PASSWORD",
                          help="connect using PASSWORD")
        self.add_argument("--host", metavar="HOST", default="localhost",
                          help="connect to HOST")
        self.add_argument("--port", metavar="PORT", default=5672,
                          help="connect to PORT", type=int)
        self.add_argument("--debug", action="store_true",
                          help="be very verbose")
        self.add_argument("--disable-dynamic-response-node",
                          action="store_true", help=_argparse.SUPPRESS)

class NodeArgumentParser(ToolArgumentParser):
    def __init__(self, *args, **kwargs):
        super(NodeArgumentParser, self).__init__(*args, **kwargs)

        self.add_argument("--node", metavar="ADDRESS", default="$management",
                          help="send requests to ADDRESS")

class ToolMain(object):
    def __init__(self, parser):
        self.parser = parser

    def main(self):
        enable_initial_logging()

        args, context = self.init()

        self.check(args, context)

        enable_console_logging("warn")

        self.run(args, context)

    def init(self):
        args = self.parser.parse_args()

        context = ClientContext()
        context.user = args.user
        context.password = args.password
        context.host = args.host
        context.port = args.port
        context.debug = args.debug

        if context.port is not None:
            try:
                context.port = int(context.port)
            except ValueError:
                self.exit("The port must be an integer")

        context._dynamic_response_node_enabled = \
            not args.disable_dynamic_response_node

        return args, context

    def check(self, args, context):
        try:
            self.do_check(args, context)
        except ToolError, e:
            self.exit(str(e))

        # try:
        #     context.check_connection()
        # except KeyboardInterrupt:
        #     raise
        # except Exception, e:
        #     self.exit(str(e))

    def do_check(self, args, context):
        pass

    def run(self, args, context):
        try:
            self.do_run(args, context)
        except (RequestError, ToolError), e:
            self.exit(str(e))

    def do_run(self, args, context):
        raise NotImplementedError()

    def exit(self, message=None):
        if message is not None:
            message = "Error: {}".format(message)

        _sys.exit(message)

class ToolError(Exception):
    pass

class _ToolHelpFormatter(_argparse.RawDescriptionHelpFormatter,
                         _argparse.ArgumentDefaultsHelpFormatter):
    pass
