# <span class="header-section-number">1</span> Qpid Management Framework

-   ?

-   ?

-   ?

-   -   ?

    -   ?

    -   ?

-   ?

-   ?

-   ?

Please visit the ? for information about the future of QMF.

## <span class="header-section-number">1.1</span> What Is QMF

QMF (Qpid Management Framework) is a general-purpose management bus
built on Qpid Messaging. It takes advantage of the scalability,
security, and rich capabilities of Qpid to provide flexible and
easy-to-use manageability to a large set of applications.

## <span class="header-section-number">1.2</span> Getting Started with QMF

QMF is used through two primary APIs. The *console* API is used for
console applications that wish to access and manipulate manageable
components through QMF. The *agent* API is used for application that
wish to be managed through QMF.

The fastest way to get started with QMF is to work through the "How To"
tutorials for consoles and agents. For a deeper understanding of what is
happening in the tutorials, it is recommended that you look at the *Qmf
Concepts* section.

## <span class="header-section-number">1.3</span> QMF Concepts

This section introduces important concepts underlying QMF.

### <span class="header-section-number">1.3.1</span> Console, Agent, and Broker

The major architectural components of QMF are the Console, the Agent,
and the Broker. Console components are the "managing" components of QMF
and agent components are the "managed" parts. The broker is a central
(possibly distributed, clustered and fault-tolerant) component that
manages name spaces and caches schema information.

A console application may be a command-line utility, a three-tiered
web-based GUI, a collection and storage device, a specialized
application that monitors and reacts to events and conditions, or
anything else somebody wishes to develop that uses QMF management data.

An agent application is any application that has been enhanced to allow
itself to be managed via QMF.

           +-------------+    +---------+    +---------------+    +-------------------+
           | CLI utility |    | Web app |    | Audit storage |    | Event correlation |
           +-------------+    +---------+    +---------------+    +-------------------+
                  ^                ^                 ^                ^          |
                  |                |                 |                |          |
                  v                v                 v                v          v
        +---------------------------------------------------------------------------------+
        |                Qpid Messaging Bus (with QMF Broker capability)                  |
        +---------------------------------------------------------------------------------+
                        ^                     ^                     ^
                        |                     |                     |
                        v                     v                     v
               +----------------+    +----------------+    +----------------+
               | Manageable app |    | Manageable app |    | Manageable app |
               +----------------+    +----------------+    +----------------+

In the above diagram, the *Manageable apps* are agents, the *CLI
utility*, *Web app*, and *Audit storage* are consoles, and *Event
correlation* is both a console and an agent because it can create events
based on the aggregation of what it sees.

### <span class="header-section-number">1.3.2</span> Schema

A *schema* describes the structure of management data. Each *agent*
provides a schema that describes its management model including the
object classes, methods, events, etc. that it provides. In the current
QMF distribution, the agent's schema is codified in an XML document. In
the near future, there will also be ways to programatically create QMF
schemata.

#### <span class="header-section-number">1.3.2.1</span> Package

Each agent that exports a schema identifies itself using a *package*
name. The package provides a unique namespace for the classes in the
agent's schema that prevent collisions with identically named classes in
other agents' schemata.

Package names are in "reverse domain name" form with levels of hierarchy
separated by periods. For example, the Qpid messaging broker uses
package "org.apache.qpid.broker" and the Access Control List plugin for
the broker uses package "org.apache.qpid.acl". In general, the package
name should be the reverse of the internet domain name assigned to the
organization that owns the agent software followed by identifiers to
uniquely identify the agent.

The XML document for a package's schema uses an enclosing \<schema\>
tag. For example:

    <schema package="org.apache.qpid.broker">

    </schema>

#### <span class="header-section-number">1.3.2.2</span> Object Classes

*Object classes* define types for manageable objects. The agent may
create and destroy objects which are instances of object classes in the
schema. An object class is defined in the XML document using the
\<class\> tag. An object class is composed of properties, statistics,
and methods.

      <class name="Exchange">
        <property name="vhostRef"   type="objId" references="Vhost" access="RC" index="y" parentRef="y"/>
        <property name="name"       type="sstr"  access="RC" index="y"/>
        <property name="type"       type="sstr"  access="RO"/>
        <property name="durable"    type="bool"  access="RC"/>
        <property name="arguments"  type="map"   access="RO" desc="Arguments supplied in exchange.declare"/>

        <statistic name="producerCount" type="hilo32"  desc="Current producers on exchange"/>
        <statistic name="bindingCount"  type="hilo32"  desc="Current bindings"/>
        <statistic name="msgReceives"   type="count64" desc="Total messages received"/>
        <statistic name="msgDrops"      type="count64" desc="Total messages dropped (no matching key)"/>
        <statistic name="msgRoutes"     type="count64" desc="Total routed messages"/>
        <statistic name="byteReceives"  type="count64" desc="Total bytes received"/>
        <statistic name="byteDrops"     type="count64" desc="Total bytes dropped (no matching key)"/>
        <statistic name="byteRoutes"    type="count64" desc="Total routed bytes"/>
      </class>

#### <span class="header-section-number">1.3.2.3</span> Properties and Statistics

\<property\> and \<statistic\> tags must be placed within \<schema\> and
\</schema\> tags.

Properties, statistics, and methods are the building blocks of an object
class. Properties and statistics are both object attributes, though they
are treated differently. If an object attribute is defining, seldom or
never changes, or is large in size, it should be defined as a
*property*. If an attribute is rapidly changing or is used to instrument
the object (counters, etc.), it should be defined as a *statistic*.

The XML syntax for \<property\> and \<statistic\> have the following
XML-attributes:

|------------|--------------|---------------|--------------------------------------------------------------------------------------------------------------------|
| Attribute  | \<property\> | \<statistic\> | Meaning                                                                                                            |
| name       | Y            | Y             | The name of the attribute                                                                                          |
| type       | Y            | Y             | The data type of the attribute                                                                                     |
| unit       | Y            | Y             | Optional unit name - use the singular (i.e. MByte)                                                                 |
| desc       | Y            | Y             | Description to annotate the attribute                                                                              |
| references | Y            |               | If the type is "objId", names the referenced class                                                                 |
| access     | Y            |               | Access rights (RC, RW, RO)                                                                                         |
| index      | Y            |               | "y" if this property is used to uniquely identify the object. There may be more than one index property in a class |
| parentRef  | Y            |               | "y" if this property references an object in which this object is in a child-parent relationship.                  |
| optional   | Y            |               | "y" if this property is optional (i.e. may be NULL/not-present)                                                    |
| min        | Y            |               | Minimum value of a numeric attribute                                                                               |
| max        | Y            |               | Maximum value of a numeric attribute                                                                               |
| maxLen     | Y            |               | Maximum length of a string attribute                                                                               |

#### <span class="header-section-number">1.3.2.4</span> Methods

\<method\> tags must be placed within \<schema\> and \</schema\> tags.

A *method* is an invokable function to be performed on instances of the
object class (i.e. a Remote Procedure Call). A \<method\> tag has a
name, an optional description, and encloses zero or more arguments.
Method arguments are defined by the \<arg\> tag and have a name, a type,
a direction, and an optional description. The argument direction can be
"I", "O", or "IO" indicating input, output, and input/output
respectively. An example:

       <method name="echo" desc="Request a response to test the path to the management broker">
         <arg name="sequence" dir="IO" type="uint32"/>
         <arg name="body"     dir="IO" type="lstr"/>
       </method>

#### <span class="header-section-number">1.3.2.5</span> Event Classes

#### <span class="header-section-number">1.3.2.6</span> Data Types

Object attributes, method arguments, and event arguments have data
types. The data types are based on the rich data typing system provided
by the AMQP messaging protocol. The following table describes the data
types available for QMF:

|-----------|--------------------------------------------------------|
| QMF Type  | Description                                            |
| REF       | QMF Object ID - Used to reference another QMF object.  |
| U8        | 8-bit unsigned integer                                 |
| U16       | 16-bit unsigned integer                                |
| U32       | 32-bit unsigned integer                                |
| U64       | 64-bit unsigned integer                                |
| S8        | 8-bit signed integer                                   |
| S16       | 16-bit signed integer                                  |
| S32       | 32-bit signed integer                                  |
| S64       | 64-bit signed integer                                  |
| BOOL      | Boolean - True or False                                |
| SSTR      | Short String - String of up to 255 bytes               |
| LSTR      | Long String - String of up to 65535 bytes              |
| ABSTIME   | Absolute time since the epoch in nanoseconds (64-bits) |
| DELTATIME | Delta time in nanoseconds (64-bits)                    |
| FLOAT     | Single precision floating point number                 |
| DOUBLE    | Double precision floating point number                 |
| UUID      | UUID - 128 bits                                        |
| FTABLE    | Field-table - std::map in C++, dictionary in Python    |

In the XML schema definition, types go by different names and there are
a number of special cases. This is because the XML schema is used in
code-generation for the agent API. It provides options that control what
kind of accessors are generated for attributes of different types. The
following table enumerates the types available in the XML format, which
QMF types they map to, and other special handling that occurs.

|-----------------|-------------|--------------------|----------------------------------------------------------|
| XML Type        | QMF Type    | Accessor Style     | Special Characteristics                                  |
| objId           | REF         | Direct (get, set)  |                                                          |
| uint8,16,32,64  | U8,16,32,64 | Direct (get, set)  |                                                          |
| int8,16,32,64   | S8,16,32,64 | Direct (get, set)  |                                                          |
| bool            | BOOL        | Direct (get, set)  |                                                          |
| sstr            | SSTR        | Direct (get, set)  |                                                          |
| lstr            | LSTR        | Direct (get, set)  |                                                          |
| absTime         | ABSTIME     | Direct (get, set)  |                                                          |
| deltaTime       | DELTATIME   | Direct (get, set)  |                                                          |
| float           | FLOAT       | Direct (get, set)  |                                                          |
| double          | DOUBLE      | Direct (get, set)  |                                                          |
| uuid            | UUID        | Direct (get, set)  |                                                          |
| map             | FTABLE      | Direct (get, set)  |                                                          |
| hilo8,16,32,64  | U8,16,32,64 | Counter (inc, dec) | Generates value, valueMin, valueMax                      |
| count8,16,32,64 | U8,16,32,64 | Counter (inc, dec) |                                                          |
| mma32,64        | U32,64      | Direct             | Generates valueMin, valueMax, valueAverage, valueSamples |
| mmaTime         | DELTATIME   | Direct             | Generates valueMin, valueMax, valueAverage, valueSamples |

> **Note**
>
> When writing a schema using the XML format, types used in \<property\>
> or \<arg\> must be types that have *Direct* accessor style. Any type
> may be used in \<statistic\> tags.

### <span class="header-section-number">1.3.3</span> Class Keys and Class Versioning

## <span class="header-section-number">1.4</span> The QMF Protocol

The QMF protocol defines the message formats and communication patterns
used by the different QMF components to communicate with one another.

A description of the current version of the QMF protocol can be found at
?.

A proposal for an updated protocol based on map-messages is in progress
and can be found at ?.

## <span class="header-section-number">1.5</span> How to Write a QMF Console

Please see the ? for information about using the console API with
Python.

## <span class="header-section-number">1.6</span> How to Write a QMF Agent
