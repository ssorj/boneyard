# <span class="header-section-number">1</span> Getting Started

# <span class="header-section-number">2</span> Introduction

This section describes how to start and stop the Java Broker, and
outlines the various command line options.

For additional details about the broker configuration store and related
command line arguments see ?. The broker is fully configurable via its
Web Management Console, for details of this see ?.

# <span class="header-section-number">3</span> Starting/Stopping the broker on Windows

Firstly change to the installation directory used during the
[installation](#Java-Broker-Installation-InstallationWindows) and ensure
that the [QPID\_WORK environment variable is
set](#Java-Broker-Installation-InstallationWindows-SettingQPIDWORK).

Now use the `qpid-server.bat` to start the server

    bin\qpid-server.bat

Output similar to the following will be seen:

    [Broker] BRK-1006 : Using configuration : C:\qpidwork\config.json
    [Broker] BRK-1007 : Using logging configuration : C:\qpid\WINDOWSEXTRACTEDBROKERDIRNAME\etc\log4j.xml
    [Broker] BRK-1001 : Startup : Version: QPIDCURRENTRELEASE Build: 1478262
    [Broker] BRK-1010 : Platform : JVM : Oracle Corporation version: 1.7.0_21-b11 OS : Windows 7 version: 6.1 arch: x86
    [Broker] BRK-1011 : Maximum Memory : 1,060,372,480 bytes
    [Broker] BRK-1002 : Starting : Listening on TCP port 5672
    [Broker] MNG-1001 : JMX Management Startup
    [Broker] MNG-1002 : Starting : RMI Registry : Listening on port 8999
    [Broker] MNG-1002 : Starting : JMX RMIConnectorServer : Listening on port 9099
    [Broker] MNG-1004 : JMX Management Ready
    [Broker] MNG-1001 : Web Management Startup
    [Broker] MNG-1002 : Starting : HTTP : Listening on port 8080
    [Broker] MNG-1004 : Web Management Ready
    [Broker] BRK-1004 : Qpid Broker Ready

The BRK-1004 message confirms that the Broker is ready for work. The
MNG-1002 and BRK-1002 confirm the ports to which the Broker is listening
(for HTTP/JMX management and AMQP respectively).

To stop the Broker, use Control-C or use the Shutdown MBean from the
[JMX management plugin](#Java-Broker-Management-Channel-JMX).

# <span class="header-section-number">4</span> Starting/Stopping the broker on Unix

Firstly change to the installation directory used during the
[installation](#Java-Broker-Installation-InstallationUnix) and ensure
that the [QPID\_WORK environment variable is
set](#Java-Broker-Installation-InstallationUnix-SettingQPIDWORK).

Now use the `qpid-server` script to start the server:

    bin/qpid-server

Output similar to the following will be seen:

    [Broker] BRK-1006 : Using configuration : /var/qpidwork/config.json
    [Broker] BRK-1007 : Using logging configuration : /usr/local/qpid/UNIXEXTRACTEDBROKERDIRNAME/etc/log4j.xml
    [Broker] BRK-1001 : Startup : Version: QPIDCURRENTRELEASE Build: exported
    [Broker] BRK-1010 : Platform : JVM : Sun Microsystems Inc. version: 1.6.0_32-b05 OS : Linux version: 3.6.10-2.fc16.x86_64 arch: amd64
    [Broker] BRK-1011 : Maximum Memory : 1,065,025,536 bytes
    [Broker] BRK-1002 : Starting : Listening on TCP port 5672
    [Broker] MNG-1001 : Web Management Startup
    [Broker] MNG-1002 : Starting : HTTP : Listening on port 8080
    [Broker] MNG-1004 : Web Management Ready
    [Broker] MNG-1001 : JMX Management Startup
    [Broker] MNG-1002 : Starting : RMI Registry : Listening on port 8999
    [Broker] MNG-1002 : Starting : JMX RMIConnectorServer : Listening on port 9099
    [Broker] MNG-1004 : JMX Management Ready
    [Broker] BRK-1004 : Qpid Broker Ready

The BRK-1004 message confirms that the Broker is ready for work. The
MNG-1002 and BRK-1002 confirm the ports to which the Broker is listening
(for HTTP/JMX management and AMQP respectively).

To stop the Broker, use Control-C from the controlling shell, use the
`bin/qpid.stop` script, use `kill -TERM <pid>`, or the Shutdown MBean
from the [JMX management plugin](#Java-Broker-Management-Channel-JMX).

# <span class="header-section-number">5</span> Log file

The Java Broker writes a log file to record both details of its normal
operation and any exceptional conditions. By default the log file is
written within the log subdirectory beneath the work directory -
`$QPID_WORK/log/qpid.log` (UNIX) and `%QPID_WORK%\log\qpid.log`
(Windows).

For details of how to control the logging, see ?

# <span class="header-section-number">6</span> Using the command line

The Java Broker understands a number of command line options which may
be used to customise the configuration.

For additional details about the broker configuration and related
command line arguments see ?. The broker is fully configurable via its
Web Management Console, for details of this see ?.

To see usage information for all command line options, use the `--help`
option

    bin/qpid-server --help

    usage: Qpid [-cic <path>] [-h] [-icp <path>] [-l <file>] [-mm] [-mmhttp <port>]
                [-mmjmx <port>] [-mmpass <password>] [-mmqv] [-mmrmi <port>] [-os]
                [-sp <path>] [-st <type>] [-v] [-w <period>]
     -cic <path>                                    Create a copy of the initial config
     --create-initial-config <path>                 file, either to an optionally specified
                                                    file path, or as initial-config.json
                                                    in the current directory

     -h,                                            Print this message
     --help

     -icp  <path>                                   Set the location of initial JSON config
     --initial-config-path <path>                   to use when creating/overwriting a
                                                    broker configuration store

     -l <file>                                      Use the specified log4j xml configuration
     --logconfig <file>                             file. By default looks for a file named
                                                    etc/log4j.xml in the same directory as
                                                    the configuration file

     -mm                                            Start broker in management mode,
     --management-mode                              disabling the AMQP ports

     -mmhttp <port>                                 Override http management port in
     --management-mode-http-port <port>             management mode

     -mmjmx                                         Override jmx connector port in
     --management-mode-jmx-connector-port <port>    management mode

     -mmpass  <password>                            Set the password for the management
     --management-mode-password <password>          mode user mm_admin

     -mmqv                                          Make virtualhosts stay in the quiesced
     --management-mode-quiesce-virtualhosts         state during management mode.

     -mmrmi <port>                                  Override jmx rmi registry port in
     --management-mode-rmi-registry-port <port>     management mode

     -os                                            Overwrite the broker configuration store
     --overwrite-store                              with the current initial configuration

     -prop "<name=value>"                           Set a configuration property to use when
     --config-property "<name=value>"               resolving variables in the broker
                                                    configuration store, with format
                                                    "name=value"

     -sp <path>                                     Use given configuration store location
     --store-path <path>

     -st <type>                                     Use given broker configuration store type
     --store-type <type>

     -v                                             Print the version information and exit
     --version

     -w <period>                                    Monitor the log file configuration file
     --logwatch <period>                            for changes. Units are seconds. Zero
                                                    means do not check for changes.
