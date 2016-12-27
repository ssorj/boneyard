# <span class="header-section-number">1</span> Operational Logging

The Broker will, by default, produce structured log messages in response
to key events in the lives of objects within the Broker. These concise
messages are designed to allow the user to understand the actions of the
Broker in retrospect. This is valuable for problem diagnosis and
provides a useful audit trail.

Each log message includes details of the entity causing the action (e.g.
a management user or messaging client connection), the entity receiving
the action (e.g. a queue or connection) and a description of operation
itself.

The log messages have the following format:

        [Actor] {[Subject]} [Message Id] [Message Text]
      

Where:

-   `Actor` is the entity within the Broker that is *performing* the
    action. There are actors corresponding to the Broker itself,
    Management, Connection, and Channels. Their format is described in
    the [table](#Java-Broker-Appendix-Operation-Logging-Actor-Format)
    below.

-   `Subject` (optional) is the entity within the Broker that is
    *receiving* the action. There are subjects corresponding to the
    Connections, Channels, Queues, Exchanges, Subscriptions, and Message
    Stores. Their format is described in the
    [table](#Java-Broker-Appendix-Operation-Logging-Subject-Format)
    below.

    Some actions are reflexive, in these cases the Actor and Subject
    will be equal.

-   `Message Id` is an identifier for the type of message. It has the
    form three alphas and four digits separated by a hyphen `AAA-9999`.

-   `Message Text` is a textual description

To illustrate, let's look at two examples.

`CON-1001` is used when a messages client makes an AMQP connection. The
connection actor (`con`) provides us with details of the peer's
connection: the user id used by the client (myapp1), their IP, ephemeral
port number and the name of the virtual host. The message text itself
gives us further details about the connection: the client id, the
protocol version in used, and details of the client's qpid library.

    [con:8(myapp1@/127.0.0.1:52851/default)] CON-1001 : Open : Client ID : clientid :
                 Protocol Version : 0-10 : Client Version : QPIDCURRENTRELEASE : Client Product : qpid

`QUE-1001` is used when a queue is created. The connection actor `con`
tells us details of the connection performing the queue creation: the
user id used by the client (myapp1), the IP, ephemeral port number and
the name of the virtual host. The queue subject tells use the queue's
name (myqueue) and the virtualhost. The message itself tells us more
information about the queue that is being created.

    [con:8(myapp1@/127.0.0.1:52851/default)/ch:0] [vh(/default)/qu(myqueue)] QUE-1001 : Create : Owner: clientid Transient

The first two tables that follow describe the actor and subject
entities, then the later provide a complete catalogue of all supported
messages.

Actors Entities

Actor Type

Format and Purpose

Broker

[Broker]

Used during startup and shutdown

Management

[mng:userid(clientip:ephemeralport)]

Used for operations performed by the either the JMX or Web Management
interfaces.

Connection

[con:connectionnumber(userid@/clientip:ephemeralport/virtualhostname)]

Used for operations performed by a client connection. Note that
connections are numbered by a sequence number that begins at 1.

Channel

[con:connectionnumber(userid@/clientip:ephemeralport/virtualhostname/ch:channelnumber)]

Used for operations performed by a client's channel (corresponds to the
JMS concept of Session). Note that channels are numbered by a sequence
number that is scoped by the owning connection.

Group

[grp(/groupname)/vhn(/virtualhostnode name)]

Used for HA. Used for operations performed by the system itself often as
a result of actions performed on another node..

Subject Entities

Subject Type

Format and Purpose

Connection

[con:connectionnumber(userid@/clientip:ephemeralport/virtualhostname)]

A connection to the Broker.

Channel

[con:connectionnumber(userid@/clientip:ephemeralport/virtualhostname/ch:channelnumber)]

A client's channel within a connection.

Subscription

[sub:subscriptionnumber(vh(/virtualhostname)/qu(queuename)]

A subscription to a queue. This corresponds to the JMS concept of a
Consumer.

Queue

[vh(/virtualhostname)/qu(queuename)]

A queue on a virtualhost

Exchange

[vh(/virtualhostname)/ex(exchangetype/exchangename)]

An exchange on a virtualhost

Binding

[vh(/virtualhostname)/ex(exchangetype/exchangename)/qu(queuename)/rk(bindingkey)]

A binding between a queue and exchange with the giving binding key.

Message Store

[vh(/virtualhostname)/ms(messagestorename)]

A virtualhost/message store on the Broker.

HA Group

[grp(/group name)]

A HA group

The following tables lists all the operation log messages that can be
produced by the Broker, and the describes the circumstances under which
each may be seen.

Broker Log Messages

Message Id

Message Text / Purpose

BRK-1001

Startup : Version: version Build: build

Indicates that the Broker is starting up

BRK-1002

Starting : Listening on transporttype port portnumber

Indicates that the Broker has begun listening on a port.

BRK-1003

Shutting down : transporttype port portnumber

Indicates that the Broker has stopped listening on a port.

BRK-1004

Qpid Broker Ready

Indicates that the Broker is ready for normal operations.

BRK-1005

Stopped

Indicates that the Broker is stopped.

BRK-1006

Using configuration : file

Indicates the name of the configuration store in use by the Broker.

BRK-1007

Using logging configuration : file

Indicates the name of the log configuration file in use by the Broker.

BRK-1008

delivered|received : size kB/s peak : size bytes total

Statistic - bytes delivered or received by the Broker.

BRK-1009

delivered|received : size msg/s peak : size msgs total

Statistic - messages delivered or received by the Broker.

BRK-1014

Message flow to disk active : Message memory use size of all messages
exceeds threshold threshold size

Indicates that the heap memory space occupied by messages has exceeded
the threshold so the flow to disk feature has been activated.

BRK-1015

Message flow to disk inactive : Message memory use size of all messages
within threshold threshold size

Indicates that the heap memory space occupied by messages has fallen
below the threshold so the flow to disk feature has been deactivated.

BRK-1016

Fatal error : root cause : See log file for more information

Indicates that broker was shut down due to fatal error.

BRK-1017

Process : PID process identifier

Process identifier (PID) of the Broker process.

Management Log Messages

Message Id

Message Text / Purpose

MNG-1001

type Management Startup

Indicates that a Management plugin is starting up. Currently supported
management plugins are JMX and Web.

MNG-1002

Starting : type : Listening on transporttype port port

Indicates that a Management plugin is listening on the given port.

MNG-1003

Shutting down : type : port port

Indicates that a Management plugin is ceasing to listen on the given
port.

MNG-1004

type Management Ready

Indicates that a Management plugin is ready for work.

MNG-1005

type Management Stopped

Indicates that a Management plugin is stopped.

MNG-1007

Open : User username

Indicates the opening of a connection to Management has by the given
username.

MNG-1008

Close : User username

Indicates the closing of a connection to Management has by the given
username.

Virtual Host Log Messages

Message Id

Message Text / Purpose

VHT-1001

Created : virtualhostname

Indicates that a virtualhost has been created.

VHT-1002

Closed

Indicates that a virtualhost has been closed. This occurs on Broker
shutdown.

VHT-1003

virtualhostname : delivered|received : size kB/s peak : size bytes total

Statistic - bytes delivered or received by the virtualhost.

VHT-1004

virtualhostname : delivered|received : size msg/s peak : size msgs total

Statistic - messages delivered or received by the virtualhost.

VHT-1005

Unexpected fatal error

Virtualhost has suffered an unexpected fatal error, check the logs for
more details.

VHT-1006

Filesystem is over size in % per cent full, enforcing flow control.

Indicates that virtual host flow control is activated when the usage of
file system containing Virtualhost message store exceeded predefined
limit.

VHT-1007

Filesystem is no longer over size in % per cent full.

Indicates that virtual host flow control is deactivated when the usage
of file system containing Virtualhost message falls under predefined
limit.

Queue Log Messages

Message Id

Message Text / Purpose

QUE-1001

Create : Owner: owner AutoDelete [Durable] Transient Priority:
numberofpriorities

Indicates that a queue has been created.

QUE-1002

Deleted

Indicates that a queue has been deleted.

QUE-1003

Overfull : Size : size bytes, Capacity : maximumsize

Indicates that a queue has exceeded its permitted capacity. See ? for
details.

QUE-1004

Underfull : Size : size bytes, Resume Capacity : resumesize

Indicates that a queue has fallen to its resume capacity. See ? for
details.

Exchange Log Messages

Message Id

Message Text / Purpose

EXH-1001

Create : [Durable] Type: type Name: exchange name

Indicates that an exchange has been created.

EXH-1002

Deleted

Indicates that an exchange has been deleted.

EXH-1003

Discarded Message : Name: exchange name Routing Key: routing key

Indicates that an exchange received a message that could not be routed
to at least one queue. queue has exceeded its permitted capacity. See ?
for details.

Binding Log Messages

Message Id

Message Text / Purpose

BND-1001

Create : Arguments : arguments

Indicates that a binding has been made between an exchange and a queue.

BND-1002

Deleted

Indicates that a binding has been deleted

Connection Log Messages

Message Id

Message Text / Purpose

CON-1001

Open : Client ID : clientid : Protocol Version : protocol version :
Client Version : client version : Client Product :client product

Indicates that a connection has been opened. The Broker logs one of
these message each time it learns more about the client as the
connection is negotiated.

CON-1002

Close

Indicates that a connection has been closed. This message is logged
regardless of if the connection is closed normally, or if the connection
is somehow lost e.g network error.

CON-1003

Closed due to inactivity

Used when heart beating is in-use. Indicates that the connection has not
received a heartbeat for too long and is therefore closed as being
inactive.

Channel Log Messages

Message Id

Message Text / Purpose

CHN-1001

Create

Indicates that a channel (corresponds to the JMS concept of Session) has
been created.

CHN-1002

Flow Started

Indicates message flow to a session has begun.

CHN-1003

Close

Indicates that a channel has been closed.

CHN-1004

Prefetch Size (bytes) size : Count number of messages

Indicates the prefetch size in use by a channel.

CHN-1005

Flow Control Enforced (Queue queue name)

Indicates that producer flow control has been imposed on a channel
owning to excessive queue depth in the indicated queue. Produces using
the channel will be requested to pause the sending of messages. See ?
for more details.

CHN-1006

Flow Control Removed

Indicates that producer flow control has been removed from a channel.
See ? for more details.

CHN-1007

Open Transaction : time ms

Indicates that a producer transaction has been open for longer than that
permitted. See ? for more details.

CHN-1008

Idle Transaction : time ms

Indicates that a producer transaction has been idle for longer than that
permitted. See ? for more details.

CHN-1009

Discarded message : message number as no alternate exchange configured
for queue : queue name{1} routing key : routing key

Indicates that a channel has discarded a message as the maximum delivery
count has been exceeded but the queue defines no alternate exchange. See
? for more details. Note that message number is an internal message
reference.

CHN-1010

Discarded message : message number as no binding on alternate exchange :
exchange name

Indicates that a channel has discarded a message as the maximum delivery
count has been exceeded but the queue's alternate exchange has no
binding to a queue. See ? for more details. Note that message number is
an internal message reference.

CHN-1011

Message : message number moved to dead letter queue : queue name

Indicates that a channel has moved a message to the named dead letter
queue

CHN-1012

Flow Control Ignored. Channel will be closed.

Indicates that a channel violating the imposed flow control has been
closed

CHN-1013

Uncommitted transaction contains size bytes of incoming message data.

Warns about uncommitted transaction with large message(s)

Subscription Log Messages

Message Id

Message Text / Purpose

SUB-1001

Create : [Durable] Arguments : arguments

Indicates that a subscription (corresponds to JMS concept of a
MessageConsumer) has been created.

SUB-1002

Close

Indicates that a subscription has been closed.

SUB-1003

SUB-1003 : Suspended for time ms

Indicates that a subscription has been in a suspened state for an
unusual length of time. This may be indicative of an consuming
application that has stopped taking messages from the consumer (i.e. a
JMS application is not calling receive() or its asynchronous message
listener onMessage() is block in application code). It may also indicate
a generally overloaded system.

Message Store Log Messages

Message Id

Message Text / Purpose

MST-1001

Created

Indicates that a message store has been created. The message store is
responsible for the storage of the messages themselves, including the
message body and any headers.

MST-1002

Store location : path

Indicates that the message store is using path for the location of the
message store.

MST-1003

Closed

Indicates that the message store has been closed.

MST-1004

Recovery Start

Indicates that message recovery has begun.

MST-1005

Recovered number of messages messages.

Indicates that recovery recovered the given number of messages from the
store.

MST-1006

Recovered Complete

Indicates that the message recovery is concluded.

MST-1007

Store Passivated

The store is entering a passive state where is it unavailable for normal
operations. Currently this message is used by HA when the node is in
replica state.

MST-1008

Store overfull, flow control will be enforced

The store has breached is maximum configured size. See ? for details.

MST-1009

Store overfull condition cleared

The store size has fallen beneath its resume capacity and therefore flow
control has been rescinded. See ? for details.

Transaction Store Log Messages

Message Id

Message Text / Purpose

TXN-1001

Created

Indicates that a transaction store has been created. The transaction
store is responsible for the storage of messages instances, that is, the
presence of a message on a queue.

TXN-1002

Store location : path

Indicates that the transaction store is using path for the location of
the store.

TXN-1003

Closed

Indicates that the transaction store has been closed.

TXN-1004

Recovery Start

Indicates that transaction recovery has begun.

TXN-1005

Recovered number messages for queue name.

Indicates that recovery recovered the given number of message instances
for the given queue.

TXN-1006

Recovered Complete

Indicates that the message recovery is concluded.

Configuration Store Log Messages

Message Id

Message Text / Purpose

CFG-1001

Created

Indicates that a configuration store has been created. The configuration
store is responsible for the storage of the definition of objects such
as queues, exchanges, and bindings.

CFG-1002

Store location : path

Indicates that the configuration store is using path for the location of
the store.

CFG-1003

Closed

Indicates that the configuration store has been closed.

CFG-1004

Recovery Start

Indicates that configuration recovery has begun.

CFG-1005

Recovered Complete

Indicates that the configuration recovery is concluded.

HA Log Messages

Message Id

Message Text / Purpose

HA-1001

Created

This HA node has been created.

HA-1002

Deleted

This HA node has been deleted

HA-1003

Added : Node : 'name' (host:port)

A new node has been added to the group.

HA-1004

Removed : Node : 'name' (host:port)

The node has been removed from the group. This removal is permanent.

HA-1005

Joined : Node : 'name' (host:port)

The node has become reachable. This may be as a result of the node being
restarted, or a network problem may have been resolved.

HA-1006

Left : Node : 'name' (host:port)

The node is no longer reachable. This may be as a result of the node
being stopped or a network partition may be preventing it from being
connected. The node is still a member of the group.

HA-1007

HA-1007 : Master transfer requested : to 'name' (host:port)

Indicates that a master transfer operation has been requested.

HA-1008

HA-1008 : Intruder detected : Node 'name' (host:port)

Indicates that an unexpected node has joined the group. The virtualhost
node will go into the ERROR state in response to the condition.

HA-1009

HA-1009 : Insufficient replicas contactable

This node (which was in the master role) no longer has sufficient
replica in contact in order to complete transactions.

HA-1010

HA-1010 : Role change reported: Node : 'name' (host:port) : from role to
role

Indicates that the node has changed role within the group.

HA-1011

HA-1011 : Minimum group size : new group size

The quorum requirements from completing elections or transactions has
been changed.

HA-1012

HA-1012 : Priority : priority

The priority of the object node has been changed. Zero indicates that
the node cannot be elected master.

HA-1013

HA-1013 : Designated primary : true|false

This node has been designated primary and can now operate solo. Applies
to two node groups only.

HA-1014

HA-1014 : Diverged transactions discarded

This node is in the process of rejoining the group but has discovered
that some of its transactions differ from those of the current master.
The node will automatically roll-back (i.e. discard) the diverging
transactions in order to be allowed to rejoin the group. This situation
can only usually occur as a result of use of the weak durability
options. These allow the group to operate with fewer than quorum nodes
and therefore allow the inconsistencies to develop.

On encountering this condition, it is *strongly* recommendend to run an
application level reconcilation to determine the data that has been
lost.

Port Log Messages

Message Id

Message Text / Purpose

PRT-1001

Create

Port has been created.

PRT-1002

Open

Port has been open

PRT-1003

Close

Port has been closed

PRT-1004

Connection count number within warn limit % of maximum limit

Warns that number of open connections approaches maximum allowed limit

PRT-1005

Connection from host rejected

Connection from given host is rejected because of reaching the maximum
allowed limit
