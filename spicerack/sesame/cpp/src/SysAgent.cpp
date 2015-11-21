#include <qpid/management/Manageable.h>
#include <qpid/management/ManagementObject.h>
#include <qpid/agent/ManagementAgent.h>
#include <qpid/sys/Mutex.h>
#include "qpid/log/Logger.h"
#include "qpid/log/SinkOptions.h"
#include "qpid/log/Statement.h"
#include "qpid/sys/SystemInfo.h"
#include "qpid/types/Uuid.h"
#include "qmf/com/redhat/sesame/Package.h"
#include "qmf/com/redhat/sesame/Sysimage.h"

#include <dbus/dbus.h> // for dbus_get_local_machine_id

#include <signal.h>
#include <unistd.h>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <sstream>

using namespace std;
using qpid::management::ManagementAgent;
using qpid::management::ManagementObject;
using qpid::management::Manageable;
using qpid::management::Args;
using qpid::sys::Mutex;
namespace _qmf = qmf::com::redhat::sesame;

static qpid::types::Uuid fixupDbusUuid(const string& in)
{
    stringstream properUuid;
    properUuid << in.substr(0,8) << "-" << in.substr(8,4) << "-" <<
        in.substr(12,4) << "-" << in.substr(16,4) << "-" <<
        in.substr(20,12);
    qpid::types::Uuid uuid;
    properUuid >> uuid;
    return uuid;
}


class SysAgent : public Manageable
{
    ManagementAgent* agent;
    _qmf::Sysimage*  mgmtObject;

public:

    SysAgent(ManagementAgent* agent, const qpid::types::Uuid& uuid);
    ~SysAgent() { mgmtObject->resourceDestroy(); }

    ManagementObject* GetManagementObject(void) const
    { return mgmtObject; }
    void run();

private:
    struct LoadAverage {
        float    load1Min;
        float    load5Min;
        float    load10Min;
        uint32_t procTotal;
        uint32_t procRunning;
    };

    struct Mem {
        uint32_t memTotal;
        uint32_t memFree;
        uint32_t swapTotal;
        uint32_t swapFree;
    };

    void setSystemId();
    void getLoadAverage(LoadAverage& la);
    void getMem(Mem& mem);
};

SysAgent::SysAgent(ManagementAgent* _agent, const qpid::types::Uuid& uuid) : agent(_agent)
{
    mgmtObject = new _qmf::Sysimage(agent, this, uuid);
    setSystemId();
    ifstream distro("/etc/redhat-release");
    if (distro.good()) {
        char text[256];
        distro.getline(text, 255);
        mgmtObject->set_distro(string(text));
        distro.close();
    }

    agent->addObject(mgmtObject, 1);
}

void SysAgent::setSystemId()
{
    std::string sysname, nodename, release, version, machine;

    qpid::sys::SystemInfo::getSystemId(sysname, nodename, release, version, machine);
    mgmtObject->set_osName(sysname);
    mgmtObject->set_nodeName(nodename);
    mgmtObject->set_release(release);
    mgmtObject->set_version(version);
    mgmtObject->set_machine(machine);
}

void SysAgent::getLoadAverage(LoadAverage& la)
{
    ifstream input("/proc/loadavg");
    if (!input.good())
        return;

    input >> la.load1Min;
    input >> la.load5Min;
    input >> la.load10Min;

    string procs;
    input >> procs;
    input.close();

    la.procTotal = 0;
    la.procRunning = 0;

    size_t slashPos = procs.find('/');
    if (slashPos == string::npos)
        return;

    la.procRunning = ::atoi(procs.substr(0, slashPos).c_str());
    la.procTotal = ::atoi(procs.substr(slashPos + 1).c_str());
}

void SysAgent::getMem(Mem& mem)
{
    ifstream input("/proc/meminfo");
    if (!input.good())
        return;

    while (!input.eof()) {
        string key;
        input >> key;
        if      (key == "MemTotal:")
            input >> mem.memTotal;
        else if (key == "MemFree:")
            input >> mem.memFree;
        else if (key == "SwapTotal:")
            input >> mem.swapTotal;
        else if (key == "SwapFree:")
            input >> mem.swapFree;
    }
    input.close();
}

void SysAgent::run()
{
    LoadAverage la;
    Mem mem;

    getMem(mem);
    mgmtObject->set_memTotal(mem.memTotal);
    mgmtObject->set_swapTotal(mem.swapTotal);

    for (;;) {
        setSystemId();
        getLoadAverage(la);
        getMem(mem);
        mgmtObject->set_loadAverage1Min(la.load1Min);
        mgmtObject->set_loadAverage5Min(la.load5Min);
        mgmtObject->set_loadAverage10Min(la.load10Min);
        mgmtObject->set_procTotal(la.procTotal);
        mgmtObject->set_procRunning(la.procRunning);

        mgmtObject->set_memFree(mem.memFree);
        mgmtObject->set_swapFree(mem.swapFree);
        mgmtObject->set_memTotal(mem.memTotal);
        mgmtObject->set_swapTotal(mem.swapTotal);
        ::sleep(5);
    }
}

struct Option {
    string placeholder;
    string defaultVal;
    string help;
    string value;

    Option() {}
    Option(const string& p, const string& d, const string& h) :
        placeholder(p), defaultVal(d), help(h), value(d) {}
};

static map<string, Option> options;

//==============================================================
// Main program
//==============================================================

ManagementAgent::Singleton* singleton;

void usage()
{
    cerr << "Usage: sesame [OPTIONS]" << endl << endl;
    for (map<string, Option>::iterator iter = options.begin();
         iter != options.end(); iter++)
        cerr << "  --" << iter->first << " " << iter->second.placeholder <<
            " (" << iter->second.defaultVal << ")  " << iter->second.help << endl;
    exit(1);
}

void configure(int argc, char** argv)
{
    // Check to see if the config file was overridden
    for (int i = 1; i < argc; i++) {
        string arg(argv[i]);
        if (arg == "--config") {
            i++;
            if (i == argc)
                usage();
            options["config"].value = string(argv[i]);
        }
        if (arg == "--no-config")
            options["config"].value = string();
        if (arg == "--help")
            usage();
    }

    // Open the config file, if present, and load its values as overrides
    // to the defaults.
    if (!options["config"].value.empty()) {
        ifstream input(options["config"].value.c_str());
        if (!input.good()) {
            QPID_LOG(error, "Can't open config file: " << options["config"].value);
            exit(1);
        }

        while (!input.eof()) {
            char line[512];
            char* cursor;
            char* val;

            input.getline(line, 512);
            if (input.fail() && !input.eof()) {
                QPID_LOG(error, "Line too long in config file: " << options["config"].value);
                exit(1);
            }

            if (line[0] != '\0' && line[0] != '#') {
                cursor = line;
                while (*cursor != '\0' && *cursor != '=')
                    cursor++;
                if (*cursor == '\0') {
                    QPID_LOG(error, "Missing value in config line: " << line);
                    exit(1);
                }
                *cursor = '\0';
                val = ++cursor;

                map<string, Option>::iterator iter = options.find(line);
                if (iter == options.end()) {
                    QPID_LOG(error, "Config file option '" << line << "' not known");
                    exit(1);
                }

                iter->second.value = string(val);
            }
        }

        input.close();
    }

    // Run through the command line options and override the defaults and the config file.
    for (int i = 1; i < argc; i++) {
        string arg(argv[i]);
        if (arg == "--no-config")
            continue;
        if (arg.substr(0, 2) != "--") {
            QPID_LOG(error, "Invalid argument: " << arg);
            usage();
        }

        map<string, Option>::iterator iter = options.find(arg.substr(2));
        if (iter == options.end()) {
            QPID_LOG(error, "Unknown option: " << arg);
            usage();
        }

        i++;
        if (i == argc) {
            QPID_LOG(error, "No value for option: " << arg);
            usage();
        }

        iter->second.value = string(argv[i]);
    }
}

void getPassword()
{
    string file(options["pwd-file"].value);
    if (file.empty())
        return;

    ifstream input(file.c_str());
    if (!input.good()) {
        QPID_LOG(error, "Can't read password file");
        exit(1);
    }

    input >> options["pwd"].value;
    input.close();
}

void shutdown(int)
{
    delete singleton;
    exit(0);
}

int main_int(int argc, char** argv)
{
    qpid::log::Logger& logger = qpid::log::Logger::instance();
    qpid::log::Options logOptions(argv[0], "sesame");

    singleton = new ManagementAgent::Singleton();
    signal(SIGINT, shutdown);

    options["no-config"]  = Option("",         "",           "Don't read configuration file");
    options["config"]     = Option("FILE",     CONF_FILE,    "Configuration file");
    options["host"]       = Option("ADDR",     "localhost",  "Broker host name or IP address");
    options["port"]       = Option("N",        "5672",       "Port for broker service");
    options["proto"]      = Option("NAME",     "tcp",        "Protocol for broker communication");
    options["mech"]       = Option("NAME",     "ANONYMOUS",  "Authentication mechanism");
    options["uid"]        = Option("NAME",     "",           "Authentication user name");
    options["pwd"]        = Option("PASSWORD", "",           "Authentication password");
    options["pwd-file"]   = Option("FILE",     "",           "File containing password");
    options["service"]    = Option("NAME",     "qpidd",      "SASL service name");
    options["min-ssf"]    = Option("N",        "0",          "Minimum acceptable strength for SASL security layer");
    options["max-ssf"]    = Option("N",        "256",        "Maximum acceptable strength for SASL security layer");
    options["state-dir"]  = Option("DIR",      LOCSTATE_DIR, "Directory for stored state");
    options["log-enable"] = Option("",         "notice+",    "Log severity threshold");
    options["pub-interval"] = Option("N",      "10",         "Publish interval in seconds");

    configure(argc, argv);
    getPassword();

    logOptions.selectors.clear();
    logOptions.selectors.push_back(options["log-enable"].value);
    logOptions.time = false;
    logger.configure(logOptions);

    // Create the qmf management agent
    ManagementAgent* agent = singleton->getInstance();

    // Register the schema with the agent
    _qmf::Package packageInit(agent);

    // Start the agent.  It will attempt to make a connection to the
    // management broker
    uint16_t interval = ::atoi(options["pub-interval"].value.c_str());
    if (interval < 1)
        interval = 10;

    qpid::management::ConnectionSettings settings;
    settings.protocol = options["proto"].value;
    settings.host = options["host"].value;
    settings.port = ::atoi(options["port"].value.c_str());
    settings.username = options["uid"].value;
    settings.password = options["pwd"].value;
    settings.mechanism = options["mech"].value;
    settings.service = options["service"].value;
    settings.minSsf = ::atoi(options["min-ssf"].value.c_str());
    settings.maxSsf = ::atoi(options["max-ssf"].value.c_str());

    char* uuid_hex = dbus_get_local_machine_id();
    if (!uuid_hex) {
        QPID_LOG(error, "Failed to acquire UUID from dbus");
        return 1;
    }

    qpid::types::Uuid uuid(fixupDbusUuid(uuid_hex));
    dbus_free(uuid_hex);

    agent->setName("redhat.com", "sesame", uuid.str());
    agent->init(settings, interval, false, options["state-dir"].value + "/agentdata");

    ::close(0);
    ::close(1);
    ::close(2);

    // Allocate core object
    SysAgent core(agent, uuid);
    core.run();
    return 0;
}

int main(int argc, char** argv)
{
    try {
        return main_int(argc, argv);
    } catch(std::exception& e) {
        QPID_LOG(error, "Top Level Exception: " << e.what());
    }
}

