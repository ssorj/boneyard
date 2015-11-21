import yaml

from optparse import *

from util import *

log = logging.getLogger("ptolemy.common.config")

class PtolemyConfig(object):
    def __init__(self, home, component):
        self.home = home
        self.component = component

        self.data = ObjectDict()
        self.data.broker = "amqp://localhost"
        self.data.log_level = "info"

    def __getattr__(self, name, default=None):
        return self.data.__getattr__(name, default)

    def get(self, path, default=None):
        tokens = path.split("/")

        value = self.data

        for token in tokens:
            try:
                value = value[token]
            except KeyError:
                log.debug("Config data:\n%s", self.data)
                raise Exception("Bad path '%s'", path)

        return value

    def load(self):
        path = os.path.join(self.home, "config", "ptolemy.config")
    
        try:
            file = open(path)
        except:
            log.info("Config file not found at '%s'", path)
            return

        try:
            sections = yaml.load(file)
        finally:
            file.close()

        #log.debug("Raw config data:\n%s", yaml.dump(sections))

        if sections:
            assert isinstance(sections, dict), sections

            if "common" in sections:
                self.update(sections["common"])

            if self.component in sections:
                self.update(sections[self.component])

    def update(self, attrs):
        self.update_data(self.data, attrs)

    def update_data(self, data, attrs):
        if attrs is None:
            return

        if not isinstance(attrs, dict):
            attrs = attrs.__dict__

        for name, value in attrs.items():
            name = name.replace("-", "_")

            if name.startswith("_"):
                continue

            if name not in data:
                continue

            if value is None:
                continue

            if isinstance(value, dict):
                self.update_data(data[name], value)
            else:
                #log.debug("Updated '%s' to '%s'", name, value)
                data[name] = value

    def __repr__(self):
        args = self.__class__.__name__, self.home
        return "%s(%s)" % args

class ObjectDict(dict):
    def __getattr__(self, name, default=None):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

class PtolemyOptionParser(OptionParser):
    def __init__(self, usage):
        OptionParser.__init__(self, usage)

        self.add_option("--broker")
        self.add_option("--log-file")
        self.add_option("--log-level", default="info")
        self.add_option("--init-only", action="store_true")

_logging_modules = ("ptolemy",)

def get_harness_id(home):
    path = os.path.join(home, "id")

    if not os.path.exists(path):
        try:
            save(path, str(uuid4()))
        except IOError:
            pass

    return load(path)
        
