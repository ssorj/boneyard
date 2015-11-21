import logging

from ConfigParser import *

log = logging.getLogger("parsley.config")

class Config(object):
    def __init__(self):
        self.sections = list()

    def parse_files(self, paths):
        parser = SafeConfigParser()
        found = parser.read(paths)

        for path in found:
            log.info("Read config file '%s'", path)

        if not found:
            log.warn("No config files found at %s", ", ".join(paths))

        sections = ConfigValues()

        for section in self.sections:
            values = section.parse(parser)
            sections[section.name] = values

        return sections

class ConfigSection(object):
    def __init__(self, config, name, strict_section=False):
        assert isinstance(config, Config)

        self.config = config
        self.config.sections.append(self)

        self.name = name
        self.strict_section = strict_section
        self.parameters = list()

    def parse(self, parser):
        in_values = dict()
        out_values = ConfigValues()

        for section in ("common", self.name):
            try:
                items = parser.items(section)
            except NoSectionError:
                if self.strict_section:
                    raise
                continue

            in_values.update(items)

        for param in self.parameters:
            try:
                string = in_values[param.name]
                value = param.unmarshal(string)
            except KeyError:
                value = param.default

            name = param.name.replace("-", "_")
            out_values[name] = value

        return out_values

class BaseConfigParameter(object):
    def __init__(self, section, name):
        assert isinstance(section, ConfigSection)

        self.section = section
        self.section.parameters.append(self)

        self.name = name
        self.default = None

    def unmarshal(self, string):
        raise Exception("Not implemented")

class ConfigParameter(BaseConfigParameter):
    def __init__(self, section, name, type):
        super(ConfigParameter, self).__init__(section, name)

        self.type = type

    def unmarshal(self, string):
        if self.type == bool:
            return string.lower() not in ("f", "false", "no", "0")
        return self.type(string)

class ConfigIntervalParameter(BaseConfigParameter):
    def unmarshal(self, value):
        mult = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'y': 31557600}
        unit = 's'

        if value[-1:].isalpha():
            unit = value[-1:]
            value = value[:-1]

        if not unit in mult:
            raise ValueError
        return float(value) * mult[unit]    

class ConfigValues(dict):
    def __getattr__(self, name):
        return self[name]
