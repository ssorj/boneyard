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
# under the License
#

from __future__ import print_function

import re as _re
import sys as _sys

from ConfigParser import SafeConfigParser as _SafeConfigParser
from collections import defaultdict as _defaultdict

class IniquityParser(_SafeConfigParser):
    def __init__(self):
        _SafeConfigParser.__init__(self)

        self._group_pattern = _re.compile(r"^(.+?):(.+)$")

    def groups(self):
        return self.sections_by_group().keys()

    def sections(self, group=None):
        return self.sections_by_group()[group]

    def sections_by_group(self):
        result = _defaultdict(list)

        for section in _SafeConfigParser.sections(self):
            group, key = self.parse_section(section)
            result[group].append(section)

        return result

    def parse_section(self, section):
        match = self._group_pattern.match(section)

        if match is None:
            return None, section

        return match.group(1), match.group(2)

def _main():
    parser = IniquityParser()

    parser.read(_sys.argv[1])

    for section in parser.sections():
        print("Section {}".format(section))

        for option in parser.options(section):
            value = parser.get(section, option)
            print("  Option {} with value {}".format(option, value))

    for group in parser.groups():
        print("Group {}".format(group))

        for section in parser.sections(group=group):
            print("  Section {}".format(section))

            for option in parser.options(section):
                value = parser.get(section, option)
                print("    Option {} with value {}".format(option, value))

if __name__ == "__main__":
    _main()
