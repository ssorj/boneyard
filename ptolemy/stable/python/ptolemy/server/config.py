import logging
import os
import socket
import sys

from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError

from util import *

log = logging.getLogger("ptolemy.config")

class Config(object):
    def __init__(self):
        self.parser = SafeConfigParser()
        self.parameters = list()

    def load_file(self, path):
        log.debug("Loading '%s'", path)

        found = self.parser.read(path)

        if not found:
            log.warn("Config file '%s' not found", path)

    def report(self):
        for param in self.parameters:
            args = (param.section, param.name, param.get())
            log.info("Parameter %s.%s = %s", *args)

class ConfigParameter(object):
    trues = ("y", "yes", "t", "true", "1")

    def __init__(self, config, section, name):
        self.config = config
        self.section = section
        self.name = name
        self.default = None
        self.type = str

        self.config.parameters.append(self)

    def unmarshal(self, string):
        if self.type is bool and string:
            value = string.lower() in self.trues
        else:
            value = self.type(string)

        return value

    def get(self):
        try:
            string = self.config.parser.get(self.section, self.name)

            try:
                value = self.unmarshal(string.strip())
            except:
                log.error("Failed unmarshaling '%s'", string)
        except NoSectionError:
            value = self.get_default()
        except NoOptionError:
            value = self.get_default()

        return value

    def get_default(self):
        return self.default

class ListParameter(ConfigParameter):
    def unmarshal(self, string):
        items = [x.strip() for x in string.split(",")]

        return items

    def get_default(self):
        return list()

class ServerConfig(Config):
    trues = ("yes", "y", "1", "t", "true")

    def __init__(self, home):
        super(ServerConfig, self).__init__()

        self.home = home
        self.debug = "PTOLEMY_DEBUG" in os.environ

        self.setup_logging()

        if self.debug:
            log.info("Debug is enabled")
        else:
            log.info("Debug is disabled")

        self.name = self.NameParameter(self, "main", "name")

        self.operator = ConfigParameter(self, "main", "operator")
        self.operator.default = "operator@example.com"

        self.broker = self.AddressParameter(self, "main", "broker")
        self.broker.default = ("localhost", 5672)

        self.web = self.AddressParameter(self, "main", "web")
        self.web.default = (socket.gethostname(), 2765)

        self.mail_enable = ConfigParameter(self, "mail", "enable")
        self.mail_enable.default = False
        self.mail_enable.type = bool

        self.mail_addrs_by_project = dict()
        self.mail_addrs_by_user = dict()

    def setup_logging(self):
        file = os.path.join(self.home, "log", "server.log")

        if self.debug:
            file_level = "debug"
            console_level = "debug"
        else:
            file_level = "debug"
            #file_level = "info" XXX
            console_level = "error"

        try:
            enable_logging("ptolemy", file_level, file)
        except IOError, e:
            print "Warning: Cannot log to file '%s': %s" % (file, e)

        enable_logging("ptolemy", console_level, sys.stderr)

    def load(self):
        path = os.path.join(self.home, "etc", "server.conf")

        self.load_file(path)

        if self.parser.has_section("mail-addrs-by-project"):
            for pattern, saddrs in self.parser.items("mail-addrs-by-project"):
                addrs = [x.strip() for x in saddrs.split(",")]
                self.mail_addrs_by_project[pattern] = addrs

        if self.parser.has_section("mail-addrs-by-user"):
            for user, saddrs in self.parser.items("mail-addrs-by-user"):
                addrs = [x.strip() for x in saddrs.split(",")]
                self.mail_addrs_by_user[user] = addrs

        self.report()

    def check(self):
        if not os.path.exists(self.home):
            raise Exception("Server home '%s' is missing", self.home)

        if not os.path.isdir(self.home):
            raise Exception("Server home '%s' is not a directory", self.home)

        if not os.access(self.home, os.X_OK | os.R_OK | os.W_OK):
            raise Exception("Server home '%s' is not accessible" % self.home)

    class NameParameter(ConfigParameter):
        def get_default(self):
            name = socket.gethostname()

            if name in ("localhost", "localhost.localdomain"):
                name = short_id()
            else:
                try:
                    name = name.split(".", 1)[0]
                except:
                    pass

            return name

    class AddressParameter(ConfigParameter):
        def unmarshal(self, string):
            addr = string.split(":", 1)

            if len(addr) > 1:
                host, port = addr[0], int(addr[1])
            else:
                host, port = addr[0], self.default[1]

            return host, port

class ProjectConfig(Config):
    def __init__(self, server, name):
        super(ProjectConfig, self).__init__()

        self.server = server
        self.name = name

        self.requires = ListParameter(self, "main", "requires")

        self.owners = ListParameter(self, "main", "owners")

        self.source = ConfigParameter(self, "main", "source")
        self.source.default = self.name

        self.install = ConfigParameter(self, "main", "install")
        self.install.default = "main"

    def load(self):
        path = os.path.join(self.server.projects_path, self.name,
                            "project.conf")

        self.load_file(path)

        self.report()
