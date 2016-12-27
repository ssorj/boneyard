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

import ConfigParser as _ConfigParser

_log = logger("pliny.config")

class _Config(object):
    def __init__(self, config_file):
        self._config_file = config_file
        self._sections = list()

        self.fallback_section = None

    def load(self):
        _log.info("Loading %s", self)

        assert self.fallback_section is None or \
            isinstance(self.fallback_section, _ConfigSection)

        self._load_options()
        self._log_options()
        self._validate_options()

    def _load_options(self):
        parser = _ConfigParser.SafeConfigParser()
        parser.read(self._config_file)

        for section in self._sections:
            for option in section._options:
                try:
                    string = parser.get(section._name, option.name)
                except _ConfigParser.NoOptionError:
                    continue

                option.load_value(string)

    def _log_options(self):
        for section in self._sections:
            for option in section._options:
                args = option, option.value, option.default_value
                _log.debug("%s has value %r (default %r)", *args)

    def _validate_options(self):
        errors = list()

        for section in self._sections:
            for option in section._options:
                if option.required and option.get_value() is None:
                    msg = "Required %s is missing" % option
                    errors.append(msg)

        if errors:
            for error in errors:
                _log.error(error)

            raise Exception("Configuration is invalid")

    def __repr__(self):
        args = self.__class__.__name__, self._config_file
        return "%s(%s)" % args
        
class _ConfigSection(object):
    def __init__(self, config, name):
        self._config = config
        self._name = name

        self._options = list()
        self._options_by_name = dict()

        self._config._sections.append(self)

    def __getattr__(self, name):
        if name.startswith("_"):
            return super(_ConfigSection, self).__getattr__(name)

        name = name.replace("_", "-")

        try:
            option = self._options_by_name[name]
        except KeyError:
            fallback = self._config.fallback_section

            if fallback is not None and fallback is not self:
                return getattr(fallback, name)

            raise AttributeError()

        return option.get_value()

class _ConfigOption(object):
    def __init__(self, section, name, default_value, cls=str, required=True):
        self.section = section
        self.name = name
        self.default_value = default_value
        self.cls = cls
        self.required = required

        self.value = None

        self.section._options.append(self)
        self.section._options_by_name[self.name] = self

    def load_value(self, string):
        self.value = self.cls(string)

    def get_value(self):
        if self.value is None:
            return self.default_value

        return self.value

    def __repr__(self):
        args = self.__class__.__name__, self.section._name, self.name
        return "%s(%s.%s)" % args

class PlinyConfig(_Config):
    def __init__(self, config_file):
        super(PlinyConfig, self).__init__(config_file)

        self.common = _ConfigSection(self, "common")

        _ConfigOption(self.common, "log-level", "info")
        _ConfigOption(self.common, "log-file", None, required=False)
        _ConfigOption(self.common, "database-file", None, required=False)

        self.web = _ConfigSection(self, "web")

        _ConfigOption(self.web, "host", "127.0.0.1")
        _ConfigOption(self.web, "port", 8080, int)
        _ConfigOption(self.web, "ssl-cert", None)
        _ConfigOption(self.web, "ssl-key", None)

        self.admin = _ConfigSection(self, "admin")

        self.fallback_section = self.common
