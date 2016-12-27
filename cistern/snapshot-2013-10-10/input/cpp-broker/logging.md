# Logging

[Up to Configuration](configuration.html)

The C++ Broker provides a rich set of logging options. To use logging
effectively a user must select a useful set of options to expose the log
messages of interest. This section introduces the logging options and
how they are used in practice.

## Concepts

### Log level

The C++ Broker has a traditional set of log severity levels. The log
levels range from low frequency and high importance critical level to
high frequency and low importance trace level.

  Name       Level
  ---------- -------
  critical   high
  error      
  warning    
  notice     
  info       
  debug      
  trace      low

  : C++ Broker Log Severity Levels

### Log category

The C++ Broker groups log messages into categories. The log category
name may then be used to enable and disable groups of related messages
at varying log levels.

  Name
  -------------
  Security
  Broker
  Management
  Protocol
  System
  HA
  Messaging
  Store
  Network
  Test
  Client
  Model
  Unspecified

  : C++ Broker Log Categories

Generally speaking the log categories are groupings of messages from
files related by thier placement in the source code directory structure.
The *Model* category is an exception. Debug log entries identified by
the Model category expose the creation, deletion, and usage statistics
for managed objects in the broker. Log messages in the Model category
are emitted by source files scattered throughout the source tree.

### Log statement attributes

Every log statement in the C++ Broker has fixed attributes that may be
used in enabling or disabling log messages.

  Name       Description
  ---------- ------------------------------------------
  Level      Severity level
  Category   Category
  Function   Namespace-qualified source function name

  : C++ Broker Log Statement Attributes

## Enabling and disabling log messages

The Qpid C++ Broker has hundreds of log message statements in the source
code. Under typical conditions most of the messages are deselected and
never emitted as actual logs. However, under some circumstances debug
and trace messages must be enabled to analyze broker behavior. This
section discusses how the broker enables and disables log messages.

At startup the broker processes command line and option file
'--log-enable RULE' and '--log-disable RULE' options using the following
rule format:

      LEVEL[+-][:PATTERN}
        

  Name         Description
  ------------ --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  LEVEL        Severity level
  [+-]         Option level modifiers. *'+'* indicates *this level and above*. *'-'* indicates *this level and below*.
  [:PATTERN]   If PATTERN matches a Category name then the log option applies only to log messages with the named category. Otherwise, the pattern is stored as a function name match string.

  : C++ Broker Log Enable/Disable RULE Format

As the options are procesed the results are aggregated into two pairs of
tables.

  Name             Description
  ---------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------
  Function Table   A set of vectors of accumulated function name patterns. There is a separate vector of name patterns for each log level.
  Category Table   A simple two dimensional array of boolean values indexed by [Level][Category] indicating if all log statements are enabled for the Level and Category pair.

  : C++ Broker Log Enable/Disable Settings Tables

--log-enable statements and --log-disable statements are aggregated into
dedicated Function and Category tables. With this scheme multiple
conflicting log enable and disable commands may be processed in any
order yet produce consistent patterns of enabled broker log statements.

## Determining if a log statement is enabled

Function Table Lookups are simple string pattern matches where the
searchable text is the domain-name qualified function name from the log
statement and the search pattern is the set of Function Table entries
for a given log level.

Category Table Lookups are boolean array queries where the Level and
Category indexes are from the log statement.

Each log statment sends its Level, Category, and FunctionName to the
Logger for evaluation. As a result the log statement is either visible
or hidden.

  Test                Description
  ------------------- -------------------------------------------------------------------------------------------------
  Disabled Function   If the statement matches a Disabled Function pattern then the statement is hidden.
  Disabled Category   If the Disabled Category table for this [Level][Category] is true then the statement is hidden.
  Enabled Function    If the statement matches a Enabled Function pattern then the statement is visible.
  Enabled Category    If the Enabled Category table for this [Level][Category] is true then the statement is visible.
  Unreferenced        Log statements that are unreferenced by specific enable rules are by default hidden.

  : C++ Broker Log Statement Visibility Determination

## Enabling and disabling logging at runtime

The C++ Broker provides QMF management methods that allow users to query
and to set the log enable and disable settings while the broker is
running.

  Method        Description
  ------------- --------------------------------------
  getLogLevel   Get the log enable/disable settings.
  setLogLevel   Set the log enable/disable settings.

  : QMF Management - Broker Methods for Managing the Log Enable/Disable
  Settings

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
          

## Discovering log sources

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
-   [3] Disables the category
    [Broker]
    and is not specific to the function. Category names supercede
    function name fragments in log option processing
-   [4] Disables the function.
-   [5] Disables the function.

Remember that the log filter matching PATTERN strings are matched
against the domain-name qualified function names associated with the log
statement and not against the log message text itself. That is, in the
previous example log filters cannot be set on the log text *Broker
running*
