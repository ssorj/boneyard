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
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import commandant as _commandant
import plano as _plano

class AbigailCommand(_commandant.Command):
    def __init__(self, home):
        super(AbigailCommand, self).__init__(home)

        self.add_argument("curr", metavar="CURRENT-LIB")
        self.add_argument("next", metavar="NEXT-LIB")

    def run(self):
        with _plano.temp_dir() as dir:
            curr_syms = set()
            next_syms = set()

            curr_out = _plano.call_for_output("nm --dynamic --demangle --defined-only {}", self.args.curr)
            next_out = _plano.call_for_output("nm --dynamic --demangle --defined-only {}", self.args.next)

            for line in curr_out.split("\n"):
                if line == "":
                    continue

                sym = line.split(" ", 2)[2]
                curr_syms.add(sym)

            for line in next_out.split("\n"):
                if line == "":
                    continue

                sym = line.split(" ", 2)[2]
                next_syms.add(sym)

            added_syms = next_syms - curr_syms
            removed_syms = curr_syms - next_syms

            print("{} {} added".format(len(added_syms), _plural("symbol", len(added_syms))))
            print("{} {} removed".format(len(removed_syms), _plural("symbol", len(removed_syms))))
            
            for sym in sorted(added_syms):
                print("Added:", sym)

            for sym in sorted(removed_syms):
                print("Removed:", sym)

def _plural(noun, count=0):
    if noun is None:
        return ""

    if count == 1:
        return noun

    if noun.endswith("s"):
        return "{}ses".format(noun)

    return "{}s".format(noun)
