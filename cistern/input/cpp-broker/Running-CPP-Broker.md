# <span class="header-section-number">1</span> Running a Qpid C++ Broker

## <span class="header-section-number">1.1</span> Building the C++ Broker and Client Libraries

The root directory for the C++ distribution is named qpidc-0.4. The
README file in that directory gives instructions for building the broker
and client libraries. In most cases you will do the following:

    [qpidc-0.4]$ ./configure
    [qpidc-0.4]$ make

## <span class="header-section-number">1.2</span> Running the C++ Broker

Once you have built the broker and client libraries, you can start the
broker from the command line:

    [qpidc-0.4]$ src/qpidd

Use the --daemon option to run the broker as a daemon process:

    [qpidc-0.4]$ src/qpidd --daemon

You can stop a running daemon with the --quit option:

    [qpidc-0.4]$ src/qpidd --quit

You can see all available options with the --help option

    [qpidc-0.4]$ src/qpidd --help

## <span class="header-section-number">1.3</span> Most common questions getting qpidd running

### <span class="header-section-number">1.3.1</span> Error when starting broker: "no data directory"

The C++ Broker requires you to set a data directory or
specify --no-data-dir (see help for more details). The data directory is
used for the journal, so it is important when reliability counts. Make
sure your process has write permission to the data directory.

The default location is

    /lib/var/qpidd

An alternate location can be set with --data-dir

### <span class="header-section-number">1.3.2</span> Error when starting broker: "that process is locked"

Note that when qpidd starts it creates a lock file is data directory are
being used. If you have a un-controlled exit, please mail the trace from
the core to the dev@qpid.apache.org mailing list. To clear the lock run

    ./qpidd -q

It should also be noted that multiple brokers can be run on the same
host. To do so set alternate data directories for each qpidd instance.

### <span class="header-section-number">1.3.3</span> Using a configuration file

Each option that can be specified on the command line can also be
specified in a configuration file. To see available options, use --help
on the command line:

    ./qpidd --help

A configuration file uses name/value pairs, one on each line. To convert
a command line option to a configuration file entry:

a.) remove the '--' from the beginning of the option. b.) place a '='
between the option and the value (use *yes* or *true* to enable options
that take no value when specified on the command line). c.) place one
option per line.

For instance, the --daemon option takes no value, the --log-to-syslog
option takes the values yes or no. The following configuration file sets
these two options:

    daemon=yes
    log-to-syslog=yes

### <span class="header-section-number">1.3.4</span> Can I use any Language client with the C++ Broker?

Yes, all the clients work with the C++ broker; it is written in C+*, but
uses the AMQP wire protocol. Any broker can be used with any client that
uses the same AMQP version. When running the C*+ broker, it is highly
recommended to run AMQP 0-10.

Note that JMS also works with the C++ broker.

## <span class="header-section-number">1.4</span> Authentication

### <span class="header-section-number">1.4.1</span> Linux

The PLAIN authentication is done on a username+password, which is stored
in the sasldb\_path file. Usernames and passwords can be added to the
file using the command:

    saslpasswd2 -f /var/lib/qpidd/qpidd.sasldb -u <REALM> <USER>

The REALM is important and should be the same as the --auth-realm option
to the broker. This lets the broker properly find the user in the sasldb
file.

Existing user accounts may be listed with:

    sasldblistusers2 -f /var/lib/qpidd/qpidd.sasldb

NOTE: The sasldb file must be readable by the user running the qpidd
daemon, and should be readable only by that user.

### <span class="header-section-number">1.4.2</span> Windows

On Windows, the users are authenticated against the local machine. You
should add the appropriate users using the standard Windows tools
(Control Panel-\>User Accounts). To run many of the examples, you will
need to create a user "guest" with password "guest".

If you cannot or do not want to create new users, you can run without
authentication by specifying the no-auth option to the broker.

## <span class="header-section-number">1.5</span> Slightly more complex configuration

The easiest way to get a full listing of the broker's options are to use
the --help command, run it locally for the latest set of options. These
options can then be set in the conf file for convenience (see above)

    ./qpidd --help

    Usage: qpidd OPTIONS
    Options:
      -h [ --help ]                    Displays the help message
      -v [ --version ]                 Displays version information
      --config FILE (/etc/qpidd.conf)  Reads configuration from FILE

    Module options:
      --module-dir DIR (/usr/lib/qpidd)  Load all .so modules in this directory
      --load-module FILE                 Specifies additional module(s) to be loaded
      --no-module-dir                    Don't load modules from module directory

    Broker Options:
      --data-dir DIR (/var/lib/qpidd)   Directory to contain persistent data generated by the broker
      --no-data-dir                     Don't use a data directory.  No persistent
                                        configuration will be loaded or stored
      -p [ --port ] PORT (5672)         Tells the broker to listen on PORT
      --worker-threads N (3)            Sets the broker thread pool size
      --max-connections N (500)         Sets the maximum allowed connections
      --connection-backlog N (10)       Sets the connection backlog limit for the
                                        server socket
      --staging-threshold N (5000000)   Stages messages over N bytes to disk
      -m [ --mgmt-enable ] yes|no (1)   Enable Management
      --mgmt-pub-interval SECONDS (10)  Management Publish Interval
      --ack N (0)                       Send session.ack/solicit-ack at least every
                                        N frames. 0 disables voluntary ack/solitict
                                       -ack

    Daemon options:
      -d [ --daemon ]             Run as a daemon.
      -w [ --wait ] SECONDS (10)  Sets the maximum wait time to initialize the
                                  daemon. If the daemon fails to initialize, prints
                                  an error and returns 1
      -c [ --check ]              Prints the daemon's process ID to stdout and
                                  returns 0 if the daemon is running, otherwise
                                  returns 1
      -q [ --quit ]               Tells the daemon to shut down
    Logging options:
      -t [ --trace ]              Enables all logging
      --log-enable RULE (notice+) Enables logging for selected levels and components. 
                                  RULE is in the form 'LEVEL[+-][:PATTERN]'
                                  LEVEL is one of: 
                                     trace debug info notice warning error critical
                                  PATTERN is a logging category name, or a namespace-qualified 
                                  function name or name fragment. 
                                     Logging category names are: 
                                     Security Broker Management Protocol System HA Messaging Store 
                                     Network Test Client Model Unspecified

                                  For example:
                                      '--log-enable warning+'
                                      logs all warning, error and critical messages.

                                      '--log-enable trace+:Broker'
                                      logs all category 'Broker' messages.

                                      '--log-enable debug:framing'
                                      logs debug messages from all functions with 'framing' in 
                                      the namespace or function name.

                                  This option can be used multiple times

      --log-disable RULE          Disables logging for selected levels and components. 
                                  RULE is in the form 'LEVEL[+-][:PATTERN]'
                                  LEVEL is one of: 
                                     trace debug info notice warning error critical
                                  PATTERN is a logging category name, or a namespace-qualified 
                                  function name or name fragment. 
                                     Logging category names are: 
                                     Security Broker Management Protocol System HA Messaging Store 
                                     Network Test Client Model Unspecified

                                  For example:
                                      '--log-disable warning-'
                                      disables logging all warning, notice, info, debug, and 
                                      trace messages.

                                      '--log-disable trace:Broker'
                                      disables all category 'Broker' trace messages.

                                      '--log-disable debug-:qmf::'
                                      disables logging debug and trace messages from all functions 
                                      with 'qmf::' in the namespace.

                                  This option can be used multiple times

      --log-time yes|no (1)                 Include time in log messages
      --log-level yes|no (1)                Include severity level in log messages
      --log-source yes|no (0)               Include source file:line in log 
                                            messages
      --log-thread yes|no (0)               Include thread ID in log messages
      --log-function yes|no (0)             Include function signature in log 
                                            messages
      --log-hires-timestamp yes|no (0)      Use hi-resolution timestamps in log 
                                            messages
      --log-category yes|no (1)             Include category in log messages
      --log-prefix STRING                   Prefix to prepend to all log messages

    Logging sink options:
      --log-to-stderr yes|no (1)            Send logging output to stderr
      --log-to-stdout yes|no (0)            Send logging output to stdout
      --log-to-file FILE                    Send log output to FILE.
      --log-to-syslog yes|no (0)            Send logging output to syslog;
                                            customize using --syslog-name and 
                                            --syslog-facility
      --syslog-name NAME (qpidd)            Name to use in syslog messages
      --syslog-facility LOG_XXX (LOG_DAEMON) 
                                            Facility to use in syslog messages

## <span class="header-section-number">1.6</span> Loading extra modules

By default the broker will load all the modules in the module directory,
however it will NOT display options for modules that are not loaded. So
to see the options for extra modules loaded you need to load the module
and then add the help command like this:

    ./qpidd --load-module libbdbstore.so --help
    Usage: qpidd OPTIONS
    Options:
      -h [ --help ]                    Displays the help message
      -v [ --version ]                 Displays version information
      --config FILE (/etc/qpidd.conf)  Reads configuration from FILE


     / .... non module options would be here ... /


    Store Options:
      --store-directory DIR     Store directory location for persistence (overrides
                                --data-dir)
      --store-async yes|no (1)  Use async persistence storage - if store supports
                                it, enables AIO O_DIRECT.
      --store-force yes|no (0)  Force changing modes of store, will delete all
                                existing data if mode is changed. Be SURE you want
                                to do this!
      --num-jfiles N (8)        Number of files in persistence journal
      --jfile-size-pgs N (24)   Size of each journal file in multiples of read
                                pages (1 read page = 64kiB)

## <span class="header-section-number">1.7</span> Timestamping Received Messages

The AMQP 0-10 specification defines a *timestamp* message delivery
property. The timestamp delivery property is a *datetime* value that is
written to each message that arrives at the broker. See the description
of "message.delivery-properties" in the "Command Classes" section of the
AMQP 0-10 specification for more detail.

See the *Programming in Apache Qpid* documentation for information
regarding how clients may access the timestamp value in received
messages.

By default, this timestamping feature is disabled. To enable
timestamping, use the *enable-timestamp* broker configuration option.
Setting the enable-timestamp option to 'yes' will enable message
timestamping:

    ./qpidd --enable-timestamp yes
      

Message timestamping can also be enabled (and disabled) without
restarting the broker. The QMF Broker management object defines two
methods for accessing the timestamp configuration:

| Method             | Description                                                                                                                   |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------|
| getTimestampConfig | Get the message timestamping configuration. Returns True if received messages are timestamped.                                |
| setTimestampConfig | Set the message timestamping configuration. Set True to enable timestamping received messages, False to disable timestamping. |

The following code fragment uses these QMF method calls to enable
message timestamping.

    # get the state of the timestamp configuration
    broker = self.qmf.getObjects(_class="broker")[0]
    rc = broker.getTimestampConfig()
    self.assertEqual(rc.status, 0)
    self.assertEqual(rc.text, "OK")
    print("The timestamp setting is %s" % str(rc.receive))

    # try to enable it
    rc = broker.setTimestampConfig(True)
    self.assertEqual(rc.status, 0)
    self.assertEqual(rc.text, "OK")
        

## <span class="header-section-number">1.8</span> Logging Options

The C++ Broker provides a rich set of logging options. To use logging
effectively a user must select a useful set of options to expose the log
messages of interest. This section introduces the logging options and
how they are used in practice.

### <span class="header-section-number">1.8.1</span> Logging Concepts

#### <span class="header-section-number">1.8.1.1</span> Log Level

The C++ Broker has a traditional set of log severity levels. The log
levels range from low frequency and high importance critical level to
high frequency and low importance trace level.

  Name                                 Level
  ------------------------------------ ------------------------------------
  critical                             high
  error                                
  warning                              
  notice                               
  info                                 
  debug                                
  trace                                low

#### <span class="header-section-number">1.8.1.2</span> Log Category

The C++ Broker groups log messages into categories. The log category
name may then be used to enable and disable groups of related messages
at varying log levels.

| Name        |
|-------------|
| Security    |
| Broker      |
| Management  |
| Protocol    |
| System      |
| HA          |
| Messaging   |
| Store       |
| Network     |
| Test        |
| Client      |
| Model       |
| Unspecified |

Generally speaking the log categories are groupings of messages from
files related by thier placement in the source code directory structure.
The *Model* category is an exception. Debug log entries identified by
the Model category expose the creation, deletion, and usage statistics
for managed objects in the broker. Log messages in the Model category
are emitted by source files scattered throughout the source tree.

#### <span class="header-section-number">1.8.1.3</span> Log Statement Attributes

Every log statement in the C++ Broker has fixed attributes that may be
used in enabling or disabling log messages.

| Name     | Description                              |
|----------|------------------------------------------|
| Level    | Severity level                           |
| Category | Category                                 |
| Function | Namespace-qualified source function name |

### <span class="header-section-number">1.8.2</span> Enabling and Disabling Log Messages

The Qpid C++ Broker has hundreds of log message statements in the source
code. Under typical conditions most of the messages are deselected and
never emitted as actual logs. However, under some circumstances debug
and trace messages must be enabled to analyze broker behavior. This
section discusses how the broker enables and disables log messages.

At startup the broker processes command line and option file
'--log-enable RULE' and '--log-disable RULE' options using the following
rule format:

      LEVEL[+-][:PATTERN}
        

| Name       | Description                                                                                                                                                                    |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| LEVEL      | Severity level                                                                                                                                                                 |
| [+-]       | Option level modifiers. *'+'* indicates *this level and above*. *'-'* indicates *this level and below*.                                                                        |
| [:PATTERN] | If PATTERN matches a Category name then the log option applies only to log messages with the named category. Otherwise, the pattern is stored as a function name match string. |

As the options are procesed the results are aggregated into two pairs of
tables.

| Name           | Description                                                                                                                                                 |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Function Table | A set of vectors of accumulated function name patterns. There is a separate vector of name patterns for each log level.                                     |
| Category Table | A simple two dimensional array of boolean values indexed by [Level][Category] indicating if all log statements are enabled for the Level and Category pair. |

--log-enable statements and --log-disable statements are aggregated into
dedicated Function and Category tables. With this scheme multiple
conflicting log enable and disable commands may be processed in any
order yet produce consistent patterns of enabled broker log statements.

### <span class="header-section-number">1.8.3</span> Determining if a Log Statement is Enabled

Function Table Lookups are simple string pattern matches where the
searchable text is the domain-name qualified function name from the log
statement and the search pattern is the set of Function Table entries
for a given log level.

Category Table Lookups are boolean array queries where the Level and
Category indexes are from the log statement.

Each log statment sends its Level, Category, and FunctionName to the
Logger for evaluation. As a result the log statement is either visible
or hidden.

| Test              | Description                                                                                     |
|-------------------|-------------------------------------------------------------------------------------------------|
| Disabled Function | If the statement matches a Disabled Function pattern then the statement is hidden.              |
| Disabled Category | If the Disabled Category table for this [Level][Category] is true then the statement is hidden. |
| Enabled Function  | If the statement matches a Enabled Function pattern then the statement is visible.              |
| Enabled Category  | If the Enabled Category table for this [Level][Category] is true then the statement is visible. |
| Unreferenced      | Log statements that are unreferenced by specific enable rules are by default hidden.            |

### <span class="header-section-number">1.8.4</span> Changing Log Enable/Disable Settings at Run Time

The C++ Broker provides QMF management methods that allow users to query
and to set the log enable and disable settings while the broker is
running.

| Method      | Description                          |
|-------------|--------------------------------------|
| getLogLevel | Get the log enable/disable settings. |
| setLogLevel | Set the log enable/disable settings. |

The management methods use a RULE format similar to the option RULE
format:

      [!]LEVEL[+-][:PATTERN]
        

The difference is the leading exclamation point that identifies disable
rules.

At start up a C++ Broker may have the following options:

      --log-enable debug+
      --log-enable trace+:Protocol
      --log-disable info-:Management
          

The following command:

      qpid-ctrl getLogLevel
          

will return the following result:

      level=debug+,trace+:Protocol,!info-:Management
          

New broker log options may be set at any time using qpid-ctrl

      qpid-ctrl setLogLevel level='debug+:Broker !debug-:broker::Broker::ManagementMethod'
          

### <span class="header-section-number">1.8.5</span> Discovering Log Sources

A common condition for a user is being swamped by log messages that are
not interesting for some debug situation. Conversely, a particular log
entry may be of interest all the time but enabling all log levels just
to see a single log entry is too much. How can a user find and specify a
pattern to single out logs of interest?

The easiest way to hide messages it to disable logs at log level and
category combinations. This may not always work since using only these
coarse controls the log messages of interest may also be hidden. To
discover a more precise filter to specify the messages you want to show
or to hide you may temporarily enable the *"--log-function=yes"* option.
The following log entries show a typical log message without and with
the log function names enabled:

      2013-05-01 11:16:01 [Broker] notice Broker running
      2013-05-01 11:16:54 [Broker] notice qpid::broker::Broker::run: Broker running
        

This log entry is emitted by function *qpid::broker::Broker::run* and
this is the function name pattern to be used in specific log enable and
disable rules. For example, this log entry could be disabled with any of
the following:

      --log-disable notice                            [1]
      --log-disable notice:qpid::                     [2]
      --log-disable notice:Broker                     [3]
      --log-disable notice-:Broker::run               [4]
      --log-disable notice:qpid::broker::Broker::run  [5]
        

-   [1] Disables all messages at notice level.
-   [2] Disables all messages at notice level in qpid:: name space. This
    is very broad and disables many log messages.
-   [3] Disables the category [Broker] and is not specific to the
    function. Category names supercede function name fragments in log
    option processing
-   [4] Disables the function.
-   [5] Disables the function.

Remember that the log filter matching PATTERN strings are matched
against the domain-name qualified function names associated with the log
statement and not against the log message text itself. That is, in the
previous example log filters cannot be set on the log text *Broker
running*
