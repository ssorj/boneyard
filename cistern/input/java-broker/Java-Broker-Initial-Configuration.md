# <span class="header-section-number">1</span> Initial Configuration

# <span class="header-section-number">2</span> Introduction

This section describes how to perform initial configuration on the
command line. Once the Broker is started, subsequent management is
performed using the [Management
interfaces](#Java-Broker-Management-Channel)

The configuration for each component is stored as an entry in the broker
configuration store, currently implemented as a JSON file which persists
changes to disk, BDB or Derby database or an in-memory store which does
not. The following components configuration is stored there:

-   Broker

-   Virtual Host

-   Port

-   Authentication Provider

-   Access Control Provider

-   Group Provider

-   Key store

-   Trust store

-   Plugin

Broker startup involves two configuration related items, the 'Initial
Configuration' and the Configuration Store. When the broker is started,
if a Configuration Store does not exist at the current [store
location](#Java-Broker-Initial-Configuration-Location) then one will be
initialised with the current ['Initial
Configuration'](#Java-Broker-Initial-Configuration-Initial-Config-Location).
Unless otherwise requested to [overwrite the configuration
store](#Java-Broker-Initial-Configuration-Location) then subsequent
broker restarts will use the existing configuration store and ignore the
contents of the 'Initial Configuration'.

# <span class="header-section-number">3</span> Configuration Store Location

The broker will default to using
[\${qpid.work\_dir}](#Java-Broker-Initial-Configuration-Configuration-Properties)/config.json
as the path for its configuration store unless otherwise instructed.

The command line argument *-sp* (or *--store-path*) can optionally be
used to specify a different relative or absolute path to use for the
broker configuration store:

    $ ./qpid-server -sp ./my-broker-configuration.json
            

If no configuration store exists at the specified/defaulted location
when the broker starts then one will be initialised using the current
['Initial
Configuration'](#Java-Broker-Initial-Configuration-Initial-Config-Location).

# <span class="header-section-number">4</span> 'Initial Configuration' Location

The 'Initial Configuration' JSON file is used when initialising new
broker configuration stores. The broker will default to using an
internal file within its jar unless otherwise instructed.

The command line argument *-icp* (or *--initial-config-path*) can be
used to override the brokers internal file and supply a [user-created
one](#Java-Broker-Initial-Configuration-Create-Initial-Config):

    $ ./qpid-server -icp ./my-initial-configuration.json
            

If a Configuration Store already exists at the current [store
location](#Java-Broker-Initial-Configuration-Location) then the current
'Initial Configuration' will be ignored unless otherwise requested to
[overwrite the configuration
store](#Java-Broker-Initial-Configuration-Location)

# <span class="header-section-number">5</span> Creating an 'Initial Configuration' JSON File

It is possible to have the broker output its default internal 'Initial
Configuration' file to disk using the command line argument *-cic* (or
*--create-initial-config*). If the option is used without providing a
path, a file called *initial-config.json* will be created in the current
directory, or alternatively the file can be created at a specified
location:

    $ ./qpid-server -cic ./initial-config.json
            

The 'Initial Configuration' JSON file shares a common format with the
brokers JSON Configuration Store implementation, so it is possible to
use a brokers Configuration Store output as an initial configuration.
Typically 'Initial Configuration' files would not to contain IDs for the
configured entities, so that IDs will be generated when the
configuration store is initialised and prevent use of the same IDs
across multiple brokers, however it may prove useful to include IDs if
using the Memory [Configuration Store
Type](#Java-Broker-Initial-Configuration-Type).

It can be useful to use [Configuration
Properties](#Java-Broker-Initial-Configuration-Configuration-Properties)
within 'Initial Configuration' files to allow a degree of customisation
with an otherwise fixed file.

For an example file, see ?

# <span class="header-section-number">6</span> Overwriting An Existing Configuration Store

If a configuration store already exists at the configured [store
location](#Java-Broker-Initial-Configuration-Location) then it is used
and the current ['Initial
Configuration'](#Java-Broker-Initial-Configuration-Initial-Config-Location)
is ignored.

The command line argument *-os* (or *--overwrite-store*) can be used to
force a new broker configuration store to be initialised from the
current 'Initial Configuration' even if one exists:

    $ ./qpid-server -os -icp ./my-initial-configuration.json
            

This can be useful to effectively play configuration into one or more
broker to pre-configure them to a particular state, or alternatively to
ensure a broker is always started with a fixed configuration. In the
latter case, use of the Memory [Configuration Store
Type](#Java-Broker-Initial-Configuration-Type) may also be useful.

# <span class="header-section-number">7</span> Configuration Store Type

There are currently two implementations of the pluggable Broker
Configuration Store, the default one which persists content to disk in a
JSON file, and another which operates only in-memory and so does not
retain changes across broker restarts and always relies on the current
['Initial
Configuration'](#Java-Broker-Initial-Configuration-Initial-Config-Location)
to provide the configuration to start the broker with.

The command line argument *-st* (or *--store-type*) can be used to
override the default *json*)configuration store type and allow choosing
an alternative, such as *memory*)

    $ ./qpid-server -st memory
            

This can be useful when running tests, or always wishing to start the
broker with the same ['Initial
Configuration'](#Java-Broker-Initial-Configuration-Initial-Config-Location)

# <span class="header-section-number">8</span> Customising Configuration using Configuration Properties

It is possible for 'Initial Configuration' (and Configuration Store)
files to contain \${properties} that can be resolved to String values at
startup, allowing a degree of customisation using a fixed file.
Configuration Property values can be set either via Java System
Properties, or by specifying ConfigurationPproperties on the broker
command line. If both are defined, System Property values take
precedence.

The broker has the following set of core configuration properties, with
the indicated default values if not otherwise configured by the user:

| Name            | Description                                                                                                                                                      | Value                                                                                                                                         |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| qpid.amqp\_port | Port number used for the brokers default AMQP messaging port                                                                                                     | "5672"                                                                                                                                        |
| qpid.http\_port | Port number used for the brokers default HTTP management port                                                                                                    | "8080"                                                                                                                                        |
| qpid.rmi\_port  | Port number used for the brokers default RMI Registry port, to advertise the JMX ConnectorServer.                                                                | "8999"                                                                                                                                        |
| qpid.jmx\_port  | Port number used for the brokers default JMX port                                                                                                                | "9099"                                                                                                                                        |
| qpid.home\_dir  | Location of the broker installation directory, which contains the 'lib' directory and the 'etc' directory often used to store files such as group and ACL files. | Defaults to the value set into the QPID\_HOME system property if it is set, or remains unset otherwise unless configured by the user.         |
| qpid.work\_dir  | Location of the broker working directory, which might contain the persistent message store and broker configuration store files.                                 | Defaults to the value set into the QPID\_WORK system property if it is set, or the 'work' subdirectory of the JVMs current working directory. |

Use of these core properties can be seen in the [default 'Initial
Configuration'
example](#Java-Broker-Configuring-And-Managing-Configuration-Initial-Config-Example).

Configuration Properties can be set on the command line using the
*-prop* (or *--configuration-property*) command line argument:

    $ ./qpid-server -prop "qpid.amqp_port=10000" -prop "qpid.http_port=10001"
            

In the example above, property used to set the port number of the
default AMQP port is specified with the value 10000, overriding the
default value of 5672, and similarly the value 10001 is used to override
the default HTTP port number of 8080. When using the 'Initial
Configuration' to initialise a new Configuration Store (either at first
broker startup, when requesting to [overwrite the configuration
store](#Java-Broker-Initial-Configuration-Location)) these new values
will be used for the port numbers instead.

NOTE: When running the broker on Windows and starting it via the
qpid-server.bat file, the "name=value" argument MUST be quoted.

# <span class="header-section-number">9</span> Example of JSON 'Initial Configuration'

An example of the default 'Initial Configuration' JSON file the broker
uses is provided below:

    {
      "name": "${broker.name}",
      "modelVersion": "2.0",
      "defaultVirtualHost" : "default",
      "authenticationproviders" : [ {
        "name" : "passwordFile",
        "type" : "PlainPasswordFile",
        "path" : "${qpid.home_dir}${file.separator}etc${file.separator}passwd",
        "preferencesproviders" : [{
            "name": "fileSystemPreferences",
            "type": "FileSystemPreferences",
            "path" : "${qpid.work_dir}${file.separator}user.preferences.json"
        }]
      } ],
      "ports" : [  {
        "name" : "AMQP",
        "port" : "${qpid.amqp_port}",
        "authenticationProvider" : "passwordFile"
      }, {
        "name" : "HTTP",
        "port" : "${qpid.http_port}",
        "authenticationProvider" : "passwordFile",
        "protocols" : [ "HTTP" ]
      }, {
        "name" : "RMI_REGISTRY",
        "port" : "${qpid.rmi_port}",
        "protocols" : [ "RMI" ]
      }, {
        "name" : "JMX_CONNECTOR",
        "port" : "${qpid.jmx_port}",
        "authenticationProvider" : "passwordFile",
        "protocols" : [ "JMX_RMI" ]
      }],
      "virtualhostnodes" : [ {
        "name" : "default",
        "type" : "JSON",
        "virtualHostInitialConfiguration" : "{ \"type\" : \"DERBY\" }"
      } ],
      "plugins" : [ {
        "type" : "MANAGEMENT-HTTP",
        "name" : "httpManagement"
      }, {
        "type" : "MANAGEMENT-JMX",
        "name" : "jmxManagement"
      } ]
    }

In the configuration above the following entries are stored:

-   Authentication Provider of type *PlainPasswordFile* with name
    "passwordFile".

-   Four Port entries: "AMQP", "HTTP", "RMI\_REGISTRY",
    "JMX\_CONNECTOR".

-   Virtualhost Node called default. On initial startup, it
    virtualHostInitialConfiguration will cause a virtualhost to be
    created with the same name. The configuration will be stored in a
    *JSON* configuration store, the message data will be stored in a
    *DERBY* message store.

-   Two management plugins: "jmxManagement" of type "MANAGEMENT-JMX" and
    "httpManagement" of type "MANAGEMENT-HTTP".

-   Broker attributes are stored as a root entry.


