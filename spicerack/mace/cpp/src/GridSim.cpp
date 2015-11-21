
#include <qpid/management/Manageable.h>
#include <qpid/management/ManagementObject.h>
#include <qpid/agent/ManagementAgent.h>
#include <qpid/sys/Mutex.h>
#include "qpid/sys/SystemInfo.h"
#include "qpid/framing/Uuid.h"
#include "qmf/com/redhat/mace/Package.h"
#include "qmf/com/redhat/sesame/Package.h"
#include "qmf/com/redhat/sesame/Sysimage.h"
#include "qmf/mrg/grid/Package.h"
#include "qmf/com/redhat/mace/GridSim.h"
#include "qmf/com/redhat/mace/ArgsGridSimStart.h"
#include "qmf/mrg/grid/Slot.h"
#include "qmf/mrg/grid/Job.h"
#include "qmf/mrg/grid/Scheduler.h"

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
using qpid::management::ObjectId;
using qpid::sys::Mutex;
using qpid::framing::Uuid;
namespace _qmf = qmf::com::redhat;
namespace _grid = qmf::mrg::grid;

class GridSim : public Manageable
{
    ManagementAgent* agent;
    _qmf::mace::GridSim* mgmtObject;
    uint32_t execNodeCount;
    uint32_t slotsPerNode;
    uint32_t slotCount;
    uint32_t jobCount;
    uint8_t  activityLevel;
    map<Uuid, ManagementObject*> systems;
    vector<ManagementObject*> slots;
    vector<ManagementObject*> jobs;
    _grid::Scheduler* scheduler;

public:

    GridSim(ManagementAgent* agent, const string& uuidFile);
    ~GridSim() { mgmtObject->resourceDestroy(); }

    ManagementObject* GetManagementObject(void) const
    { return mgmtObject; }
    void run();
    Manageable::status_t ManagementMethod (uint32_t methodId, Args& args, string& text);
};

GridSim::GridSim(ManagementAgent* _agent, const string& uuidFile) :
    agent(_agent), mgmtObject(new _qmf::mace::GridSim(agent, this)),
    execNodeCount(0), slotsPerNode(0), slotCount(0),
    jobCount(0), activityLevel(0), scheduler(0)
{
    mgmtObject->set_execNodeCount(execNodeCount);
    mgmtObject->set_slotsPerNode(slotsPerNode);
    mgmtObject->set_slotCount(slotCount);
    mgmtObject->set_jobCount(jobCount);
    mgmtObject->set_activityLevel(activityLevel);

    agent->addObject(mgmtObject, 1);
}

void GridSim::run()
{
    for (;;) {
        ::sleep(5);
    }
}

Manageable::status_t GridSim::ManagementMethod(uint32_t methodId, Args& args, string& text)
{
    if (methodId == _qmf::mace::GridSim::METHOD_RESET) {
        for (map<Uuid, ManagementObject*>::iterator iter = systems.begin();
             iter != systems.end(); iter++)
            iter->second->resourceDestroy();
        systems.clear();

        for (vector<ManagementObject*>::iterator iter = slots.begin();
             iter != slots.end(); iter++)
            (*iter)->resourceDestroy();
        slots.clear();

        for (vector<ManagementObject*>::iterator iter = jobs.begin();
             iter != jobs.end(); iter++)
            (*iter)->resourceDestroy();
        jobs.clear();

        if (scheduler) {
            scheduler->resourceDestroy();
            scheduler = 0;
        }

        return STATUS_OK;
    }
    else if (methodId == _qmf::mace::GridSim::METHOD_START) {
        _qmf::mace::ArgsGridSimStart& ioArgs = (_qmf::mace::ArgsGridSimStart&) args;
        cout << "START: nodes=" << ioArgs.i_execNodes << " s/n=" << ioArgs.i_slotsPerNode <<
            " jobs=" << ioArgs.i_jobs << " act=" << (int) ioArgs.i_activity << endl;

        mgmtObject->set_execNodeCount(ioArgs.i_execNodes);
        mgmtObject->set_slotsPerNode(ioArgs.i_slotsPerNode);
        mgmtObject->set_slotCount(ioArgs.i_execNodes * ioArgs.i_slotsPerNode);
        mgmtObject->set_jobCount(ioArgs.i_jobs);
        mgmtObject->set_activityLevel(ioArgs.i_activity);

        string schedSysName;

        // Do scheduler
        scheduler = new _grid::Scheduler(agent, this);
        scheduler->set_Pool("Pool");
        scheduler->set_System(schedSysName);

        // Do systems
        for (uint32_t i = 0; i < ioArgs.i_execNodes; i++) {
            Uuid uuid(true);
            _qmf::sesame::Sysimage* si(new _qmf::sesame::Sysimage(agent, this, uuid));
            si->set_osName("Linux");
            si->set_nodeName("dhcp-100-18-254.bos.redhat.com");
            si->set_release("2.6.26.6-49.fc8");
            si->set_version("#1 SMP Fri Oct 17 15:59:36 EDT 2008");
            si->set_machine("i686");
            si->set_memTotal(4096);
            si->set_swapTotal(8192);
            agent->addObject(si);
            systems[uuid] = si;

            if (i == 0) {
                stringstream id;
                id << uuid;
                schedSysName = id.str();
            }
        }

        // Do scheduler
        scheduler = new _grid::Scheduler(agent, this);
        scheduler->set_Pool("Pool");
        scheduler->set_System(schedSysName);
        ObjectId schedId = agent->addObject(scheduler);

        // Do slots
        for (map<Uuid, ManagementObject*>::iterator iter = systems.begin();
             iter != systems.end(); iter++) {
            stringstream id;
            id << iter->first;

            for (uint32_t i = 0; i < ioArgs.i_slotsPerNode; i++) {
                _grid::Slot* slot(new _grid::Slot(agent, this));
                slot->set_Pool("Pool");
                slot->set_System(id.str());
                agent->addObject(slot);
                slots.push_back(slot);
            }
        }

        // Do jobs
        for (uint32_t i = 0; i < ioArgs.i_jobs; i++) {
            _grid::Job* job(new _grid::Job(agent, this));
            job->set_schedulerRef(schedId);
            agent->addObject(job);
            jobs.push_back(job);
        }

        return STATUS_OK;
    }
    return STATUS_NOT_IMPLEMENTED;
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
            cerr << "Can't open config file: " << options["config"].value << endl;
            exit(1);
        }

        while (!input.eof()) {
            char line[512];
            char* cursor;
            char* val;

            input.getline(line, 512);
            if (input.fail() && !input.eof()) {
                cerr << "Line too long in config file: " << options["config"].value << endl;
                exit(1);
            }

            if (line[0] != '\0' && line[0] != '#') {
                cursor = line;
                while (*cursor != '\0' && *cursor != '=')
                    cursor++;
                if (*cursor == '\0') {
                    cerr << "Missing value in config line: " << line << endl;
                    exit(1);
                }
                *cursor = '\0';
                val = ++cursor;

                map<string, Option>::iterator iter = options.find(line);
                if (iter == options.end()) {
                    cerr << "Config file option '" << line << "' not known" << endl;
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
            cerr << "Invalid argument: " << arg << endl;
            usage();
        }

        map<string, Option>::iterator iter = options.find(arg.substr(2));
        if (iter == options.end()) {
            cerr << "Unknown option: " << arg << endl;
            usage();
        }

        i++;
        if (i == argc) {
            cerr << "No value for option: " << arg << endl;
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
        cerr << "Can't read password file" << endl;
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
    singleton = new ManagementAgent::Singleton();
    signal(SIGINT, shutdown);

    options["no-config"] = Option("",         "",           "Don't read configuration file");
    options["config"]    = Option("FILE",     CONF_FILE,    "Configuration file");
    options["host"]      = Option("ADDR",     "localhost",  "Broker host name or IP address");
    options["port"]      = Option("N",        "5672",       "Port for broker service");
    options["proto"]     = Option("NAME",     "tcp",        "Protocol for broker communication");
    options["mech"]      = Option("NAME",     "PLAIN",      "Authentication mechanism");
    options["uid"]       = Option("NAME",     "guest",      "Authentication user name");
    options["pwd"]       = Option("PASSWORD", "guest",      "Authentication password");
    options["pwd-file"]  = Option("FILE",     "",           "File containing password");
    options["state-dir"] = Option("DIR",      LOCSTATE_DIR, "Directory for stored state");

    configure(argc, argv);
    getPassword();

    // Create the qmf management agent
    ManagementAgent* agent = singleton->getInstance();

    // Register the schema with the agent
    _qmf::mace::Package mPackageInit(agent);
    _qmf::sesame::Package sPackageInit(agent);
    _grid::Package gPackageInit(agent);

    // Start the agent.  It will attempt to make a connection to the
    // management broker
    agent->init(options["host"].value, ::atoi(options["port"].value.c_str()), 5, false,
                options["state-dir"].value + "/agentdata",
                options["uid"].value, options["pwd"].value,
                options["mech"].value, options["proto"].value);

    // Allocate core object
    GridSim core(agent, options["state-dir"].value + "/uuid");
    core.run();
}

int main(int argc, char** argv)
{
    try {
        return main_int(argc, argv);
    } catch(std::exception& e) {
        cout << "Top Level Exception: " << e.what() << endl;
    }
}

