from optparse import OptionParser

from parsley.config import *
from parsley.loggingex import *

from util import *

log = logging.getLogger("cumin.config")

class CuminConfig(Config):
    def __init__(self, section_name):
        super(CuminConfig, self).__init__()

        hdef = os.path.normpath("/usr/share/cumin")
        self.home = os.environ.get("CUMIN_HOME", hdef)

        if not os.path.isdir(self.home):
            raise Exception("Home path '%s' is not a directory")

        # Remember the config section we were created with
        self.section_name = section_name

    def get_home(self):
        return self.home

    def get_access_root(self):
        return os.path.join(self.home, "model/access/")

    def get_init_status_path(self, section_name=""):
        if not section_name:
            section_name = self.section_name
        if section_name:
            return os.path.join(self.home, "log", "." + section_name + ".init")
        return ""

    def expand_log_file(self, log_file):
        # If log_file begins with a / it's absolute and we
        # leave it alone.  If not, it's relative to $CUMIN_HOME/log
        if not log_file or log_file.startswith("/"):
            return log_file
        return os.path.join(self.home, "log", log_file)

    def parse(self):
        paths = list()

        paths.append(os.path.join(os.sep, "etc", "cumin", "cumin.conf"))
        paths.append(os.path.join(self.home, "etc", "cumin.conf"))
        paths.append(os.path.join(os.path.expanduser("~"), ".cumin.conf"))

        return self.parse_files(paths)

class CuminCommonConfig(CuminConfig):
    '''
    Provide a simple class which just gives access
    to the values in the common section of the config
    file for apps which do not need any more
    '''
    def __init__(self):
        super(CuminCommonConfig, self).__init__("common")

        self.section = CuminConfigSection(self, self.section_name)

    def set_log(self, log):
        self.section.log_file.default = log

class CuminWebConfig(CuminConfig):
    def __init__(self, section_name="web", strict_section="False"):
        super(CuminWebConfig, self).__init__(section_name)

        web = CuminWebConfigSection(self, self.section_name, strict_section)
        web.log_file.default = os.path.join(self.home, "log", 
                                            self.section_name + ".log")

def _common_data_section(self, data, name):
    data.log_file.default = os.path.join(self.home, "log", name + ".log")

    param = ConfigParameter(data, "include-classes", str)
    param = ConfigParameter(data, "exclude-classes", str)

    param = ConfigParameter(data, "expire-enabled", bool)
    param.default = True

    param = ConfigIntervalParameter(data, "expire-interval")
    param.default = 60 * 60 # 1 hour

    param = ConfigIntervalParameter(data, "expire-threshold")
    param.default = 24 * 60 * 60 # 1 day

    param = ConfigParameter(data, "vacuum-enabled", bool)
    param.default = True

    param = ConfigIntervalParameter(data, "vacuum-interval")
    param.default = 60 * 60 # 1 hour    
    
class CuminDataConfig(CuminConfig):
    def __init__(self, section_name="data", strict_section=False):
        super(CuminDataConfig, self).__init__(section_name)

        data = CuminDataConfigSection(self, self.section_name, strict_section)
        _common_data_section(self, data, self.section_name)

class CuminReportConfig(CuminConfig):
    def __init__(self, section_name="report", strict_section=False):
        super(CuminReportConfig, self).__init__(section_name)

        data = CuminReportConfigSection(self, 
                                        self.section_name, strict_section)
        _common_data_section(self, data, self.section_name)

class CuminMasterConfig(CuminConfig):
    def __init__(self, section_name="master", strict_section=False):
        super(CuminMasterConfig, self).__init__(section_name)

        master = ConfigSection(self, self.section_name, strict_section)
        param = ConfigParameter(master, "datas", str)
        param.default = "data"

        param = ConfigParameter(master, "webs", str)
        param.default = "web"

        param = ConfigParameter(master, "reports", str)
        param.default = ""

class CuminConfigSection(ConfigSection):
    def __init__(self, config, name, strict_section=False):
        super(CuminConfigSection, self).__init__(config, name, strict_section)

        param = ConfigParameter(self, "database", str)
        param.default = "dbname=cumin"

        # Put this here, because authentication is something that
        # might need to be done commonly
        param = ConfigParameter(self, "auth", str)
        param.default = ""

        param = ConfigParameter(self, "ldap_tls_cacertfile", str)
        param.default = ""

        param = ConfigParameter(self, "ldap_tls_cacertdir", str)
        param.default = ""

        param = ConfigParameter(self, "ldap_timeout", int)
        param.default  = 30

        self.log_file = ConfigParameter(self, "log-file", str)

        param = ConfigParameter(self, "log-level", str)
        param.default = "info"

        param = ConfigParameter(self, "log-max-mb", float)
        param.default = 10

        param = ConfigParameter(self, "log-max-archives", int)
        param.default = 1

        param = ConfigParameter(self, "debug", bool)
        param.default = False

class BrokeredConfigSection(CuminConfigSection):
    def __init__(self, config, name, strict_section=False):
        super(BrokeredConfigSection, self).__init__(config, name, 
                                                    strict_section)

        param = ConfigParameter(self, "brokers", str)
        param.default = "amqp://localhost"

        # Leave default set to None, which is equivalent to 
        # previous behavior
        param = ConfigParameter(self, "sasl-mech-list", str)

class CuminWebConfigSection(BrokeredConfigSection):
    def __init__(self, config, name, strict_section=False):
        super(CuminWebConfigSection, self).__init__(config, name, 
                                                    strict_section)

        # Turn this into a boolean, default is off for introduction.
        # Hardwire the path to persona.xml unless/until we allow overriding
        param = ConfigParameter(self, "authorize", bool)
        param.default = False

        param = ConfigParameter(self, "force-secure-cookies", bool)
        param.default = False

#        param = ConfigParameter(self, "auth-proxy", bool)
#        param.default = False

        param = ConfigParameter(self, "wallaby-broker", str)
        param.default = ""

        param = ConfigParameter(self, "wallaby-refresh", int)
        param.default = 60

        param = ConfigParameter(self, "aviary-job-servers", str)
        param.default = "http://localhost:9090"

        param = ConfigParameter(self, "aviary-query-servers", str)
        param.default = "http://localhost:9091"

        param = ConfigParameter(self, "aviary-locator", str)
        param.default = ""

        param = ConfigParameter(self, "aviary-key", str)
        param.default = ""

        param = ConfigParameter(self, "aviary-cert", str)
        param.default = ""

        param = ConfigParameter(self, "aviary-root-cert", str)
        param.default = ""

        param = ConfigParameter(self, "aviary-domain-verify", bool)
        param.default = True
        
        # Intended for development use, not the end user.
        # Undocumented.
        param = ConfigParameter(self, "aviary-suds-logs", bool)
        param.default = False

        # By default, Cumin will look for aviary wsdl files in
        # /var/lib/condor/aviary/services before it looks to the
        # wsdl files bundled with Cumin.
        # If this flag is set to False, it will look at the files
        # bundled with Cumin first.
        # Undocumented.
        param = ConfigParameter(self, "aviary-prefer-condor", bool)
        param.default = True

        param = ConfigParameter(self, "server-cert", str)
        param.default = ""

        param = ConfigParameter(self, "server-key", str)
        param.default = ""

        param = ConfigIntervalParameter(self, "update-interval")
        param.default = 10

        param = ConfigParameter(self, "max-qmf-table-sort", int)
        param.default = 1000

        param = ConfigParameter(self, "host", str)
        param.default = "localhost"

        param = ConfigParameter(self, "port", int)
        param.default = 45672

        param = ConfigParameter(self, "operator-email", str)

        param = ConfigParameter(self, "user", str)

        param = ConfigParameter(self, "request-memory",    int)
        param.default = 512 # MB
        param = ConfigParameter(self, "request-memory-vm", int)
        param.default = 512 # MB
        param = ConfigParameter(self, "request-disk",      int)
        param.default = 1024 #MB
        param = ConfigParameter(self, "request-disk-vm",   int)
        param.default = 5 * 1024 #MB

        param = ConfigParameter(self, "persona", str)
        param.default = "grid"
        
        param = ConfigParameter(self, "fast-view-attributes", str)
        param.default = "JobStatus,Cmd,Args,ExitStatus,JobStartDate,"\
                        "LastRemoteHost,LastJobStatus,Owner"
        
        param = ConfigParameter(self, "notification-timeout", int)
        param.default = 180
        
        # Hidden parameter used to force html doctype rather than xhtml
        # This is hopefully a temporary workaround so that selenium can 
        # be used to do some automated testing against cumin
        param = ConfigParameter(self, "force-html-doctype", bool)
        param.default = False

class CuminDataConfigSection(BrokeredConfigSection):
    def __init__(self, config, name, strict_section=False):
        super(CuminDataConfigSection, self).__init__(config, name, 
                                                     strict_section)
        param = ConfigParameter(self, "agents", str)

class CuminReportConfigSection(CuminConfigSection):
    def __init__(self, config, name, strict_section=False):
        super(CuminReportConfigSection, self).__init__(config, name, 
                                                      strict_section)

        param = ConfigParameter(self, "plumage_host", str)
        param.default = "localhost"
        
        param = ConfigParameter(self, "plumage_port", int)
        param.default = 27017

class CuminOptionParser(OptionParser,object):
    def __init__(self):
        OptionParser.__init__(self)

        self.add_option("--init-only", action="store_true", default=False)
        self.add_option("--es", default="")

        self.add_option("--tm", default="5", type=int)


        # Defaults for these come later from the config
        # section named in --section, via apply_defaults()
        self.add_option("--debug", action="store_true")
        self.add_option("--database")
        self.add_option("--log-file")
        self.add_option("--log-level")

class BrokeredOptionParser(CuminOptionParser):
    def __init__(self):
        CuminOptionParser.__init__(self)

        # Defaults for these come later from the config
        # section named in --section, via apply_defaults()
        self.add_option("--brokers")

class PlumageOptionParser(CuminOptionParser):
    def __init__(self):
        CuminOptionParser.__init__(self)

        # Defaults for these come later from the config
        # section named in --section, via apply_defaults()
        self.add_option("--server")

def apply_defaults(values, opts):
    for k, v in opts.__dict__.iteritems():
        if v == None and k in values:
            opts.__dict__[k] = values[k]

# These logging functions address a logging bootstrap problem.  Before
# configuration is read, we can't configure logging.  Nonetheless,
# we'd like to log errors or warnings encountered before that point.
# These logging functions split setup into two phases, the first being
# temporary and basic, and the second being fully configured.
#
# Here's how to use them:
#
#     def main():
#         setup_initial_logging()
#
#         # load config files and command-line options
#
#         setup_operational_logging(config)
#
#         # start your business

_logging_modules = "cumin", "mint", "parsley", "rosemary", "wooly", "sage"

def setup_initial_logging():
    for name in _logging_modules:
        enable_logging(name, "warn", sys.stderr)

def setup_operational_logging(values, log_max_mb=10, log_max_archives=1):
    for name in _logging_modules:
        disable_logging(name)
        enable_logging(name, values.log_level, values.log_file, 
                             log_max_mb, log_max_archives)

    if values.debug:
        for name in _logging_modules:
            enable_logging(name, "debug", sys.stderr)
