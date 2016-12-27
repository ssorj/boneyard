# <span class="header-section-number">1</span> Broker Federation

Broker Federation allows messaging networks to be defined by creating
message routes, in which messages in one broker (the source broker) are
automatically routed to another broker (the destination broker). These
routes may be defined between exchanges in the two brokers (the source
exchange and the destination exchange), or from a queue in the source
broker (the source queue) to an exchange in the destination broker.
Message routes are unidirectional; when bidirectional flow is needed,
one route is created in each direction. Routes can be durable or
transient. A durable route survives broker restarts, restoring a route
as soon as both the source broker and the destination are available. If
the connection to a destination is lost, messages associated with a
durable route continue to accumulate on the source, so they can be
retrieved when the connection is reestablished.

Broker Federation can be used to build large messaging networks, with
many brokers, one route at a time. If network connectivity permits, an
entire distributed messaging network can be configured from a single
location. The rules used for routing can be changed dynamically as
servers change, responsibilities change, at different times of day, or
to reflect other changing conditions.

Broker Federation is useful in a wide variety of scenarios. Some of
these have to do with functional organization; for instance, brokers may
be organized by geography, service type, or priority. Here are some use
cases for federation:

-   Geography: Customer requests may be routed to a processing location
    close to the customer.

-   Service Type: High value customers may be routed to more responsive
    servers.

-   Load balancing: Routing among brokers may be changed dynamically to
    account for changes in actual or anticipated load.

-   High Availability: Routing may be changed to a new broker if an
    existing broker becomes unavailable.

-   WAN Connectivity: Federated routes may connect disparate locations
    across a wide area network, while clients connect to brokers on
    their own local area network. Each broker can provide persistent
    queues that can hold messages even if there are gaps in WAN
    connectivity.

-   Functional Organization: The flow of messages among software
    subsystems can be configured to mirror the logical structure of a
    distributed application.

-   Replicated Exchanges: High-function exchanges like the XML exchange
    can be replicated to scale performance.

-   Interdepartmental Workflow: The flow of messages among brokers can
    be configured to mirror interdepartmental workflow at an
    organization.

## <span class="header-section-number">1.1</span> Message Routes

Broker Federation is done by creating message routes. The destination
for a route is always an exchange on the destination broker. By default,
a message route is created by configuring the destination broker, which
then contacts the source broker to subscribe to the source queue. This
is called a pull route. It is also possible to create a route by
configuring the source broker, which then contacts the destination
broker in order to send messages. This is called a push route, and is
particularly useful when the destination broker may not be available at
the time the messaging route is configured, or when a large number of
routes are created with the same destination exchange.

The source for a route can be either an exchange or a queue on the
source broker. If a route is between two exchanges, the routing criteria
can be given explicitly, or the bindings of the destination exchange can
be used to determine the routing criteria. To support this
functionality, there are three kinds of message routes: queue routes,
exchange routes, and dynamic exchange routes.

### <span class="header-section-number">1.1.1</span> Queue Routes

Queue Routes route all messages from a source queue to a destination
exchange. If message acknowledgement is enabled, messages are removed
from the queue when they have been received by the destination exchange;
if message acknowledgement is off, messages are removed from the queue
when sent.

### <span class="header-section-number">1.1.2</span> Exchange Routes

Exchange routes route messages from a source exchange to a destination
exchange, using a binding key (which is optional for a fanout exchange).

Internally, creating an exchange route creates a private queue
(auto-delete, exclusive) on the source broker to hold messages that are
to be routed to the destination broker, binds this private queue to the
source broker exchange, and subscribes the destination broker to the
queue.

### <span class="header-section-number">1.1.3</span> Dynamic Exchange Routes

Dynamic exchange routes allow a client to create bindings to an exchange
on one broker, and receive messages that satisfy the conditions of these
bindings not only from the exchange to which the client created the
binding, but also from other exchanges that are connected to it using
dynamic exchange routes. If the client modifies the bindings for a given
exchange, they are also modified for dynamic exchange routes associated
with that exchange.

Dynamic exchange routes apply all the bindings of a destination exchange
to a source exchange, so that any message that would match one of these
bindings is routed to the destination exchange. If bindings are added or
removed from the destination exchange, these changes are reflected in
the dynamic exchange route -- when the destination broker creates a
binding with a given binding key, this is reflected in the route, and
when the destination broker drops a binding with a binding key, the
route no longer incurs the overhead of transferring messages that match
the binding key among brokers. If two exchanges have dynamic exchange
routes to each other, then all bindings in each exchange are reflected
in the dynamic exchange route of the other. In a dynamic exchange route,
the source and destination exchanges must have the same exchange type,
and they must have the same name; for instance, if the source exchange
is a direct exchange, the destination exchange must also be a direct
exchange, and the names must match.

Internally, dynamic exchange routes are implemented in the same way as
exchange routes, except that the bindings used to implement dynamic
exchange routes are modified if the bindings in the destination exchange
change.

A dynamic exchange route is always a pull route. It can never be a push
route.

## <span class="header-section-number">1.2</span> Federation Topologies

A federated network is generally a tree, star, or line, using
bidirectional links (implemented as a pair of unidirectional links)
between any two brokers. A ring topology is also possible, if only
unidirectional links are used.

Every message transfer takes time. For better performance, you should
minimize the number of brokers between the message origin and final
destination. In most cases, tree or star topologies do this best.

For any pair of nodes A,B in a federated network, there should be only
one path from A to B. If there is more than one path, message loops can
cause duplicate message transmission and flood the federated network.
The topologies discussed above do not have message loops. A ring
topology with bidirectional links is one example of a topology that does
cause this problem, because a given broker can receive the same message
from two different brokers. Mesh topologies can also cause this problem.

## <span class="header-section-number">1.3</span> Federation among High Availability Message Clusters

Federation is generally used together with High Availability Message
Clusters, using clusters to provide high availability on each LAN, and
federation to route messages among the clusters. Because message state
is replicated within a cluster, it makes little sense to define message
routes between brokers in the same cluster.

To create a message route between two clusters, simply create a route
between any one broker in the first cluster and any one broker in the
second cluster. Each broker in a given cluster can use message routes
defined for another broker in the same cluster. If the broker for which
a message route is defined should fail, another broker in the same
cluster can restore the message route.

## <span class="header-section-number">1.4</span> The qpid-route Utility

`qpid-route` is a command line utility used to configure federated
networks of brokers and to view the status and topology of networks. It
can be used to configure routes among any brokers that `qpid-route` can
connect to.

The syntax of `qpid-route` is as follows:

          qpid-route [OPTIONS] dynamic add <dest-broker> <src-broker> <exchange>
          qpid-route [OPTIONS] dynamic del <dest-broker> <src-broker> <exchange>

          qpid-route [OPTIONS] route add <dest-broker> <src-broker> <exchange> <routing-key>
          qpid-route [OPTIONS] route del <dest-broker> <src-broker> <exchange> <routing-key>

          qpid-route [OPTIONS] queue add <dest-broker> <src-broker> <dest-exchange>  <src-queue>
          qpid-route [OPTIONS] queue del <dest-broker> <src-broker> <dest-exchange>  <src-queue>

          qpid-route [OPTIONS] list  [<broker>]
          qpid-route [OPTIONS] flush [<broker>]
          qpid-route [OPTIONS] map   [<broker>]

          
          qpid-route [OPTIONS] list connections [<broker>]
        

The syntax for `broker`, `dest-broker`, and `src-broker` is as follows:

          [username/password@] hostname | ip-address [:<port>]
        

The following are all valid examples of the above syntax: `localhost`,
`10.1.1.7:10000`, `broker-host:10000`, `guest/guest@localhost`.

These are the options for `qpid-route`:

<table>
<caption><code>qpid-route</code> options</caption>
<colgroup>
<col width="50%" />
<col width="50%" />
</colgroup>
<tbody>
<tr class="odd">
<td align="left"><code>-v</code></td>
<td align="left">Verbose output.</td>
</tr>
<tr class="even">
<td align="left"><code>-q</code></td>
<td align="left">Quiet output, will not print duplicate warnings.</td>
</tr>
<tr class="odd">
<td align="left"><code>-d</code></td>
<td align="left">Make the route durable.</td>
</tr>
<tr class="even">
<td align="left"><code> --timeout N</code></td>
<td align="left">Maximum time to wait when qpid-route connects to a broker, in seconds. Default is 10 seconds.</td>
</tr>
<tr class="odd">
<td align="left"><code>--ack N</code></td>
<td align="left">Acknowledge transfers of routed messages in batches of N. Default is 0 (no acknowledgements). Setting to 1 or greater enables acknowledgements; when using acknowledgements, values of N greater than 1 can significnantly improve performance, especially if there is significant network latency between the two brokers.</td>
</tr>
<tr class="even">
<td align="left"><code>-s [ --src-local ]</code></td>
<td align="left">Configure the route in the source broker (create a push route).</td>
</tr>
<tr class="odd">
<td align="left"><code>-t &lt;transport&gt; [ --transport &lt;transport&gt;]</code></td>
<td align="left">Transport protocol to be used for the route.
<ul>
<li><p>tcp (default)</p></li>
<li><p>ssl</p></li>
<li><p>rdma</p></li>
</ul></td>
</tr>
</tbody>
</table>

### <span class="header-section-number">1.4.1</span> Creating and Deleting Queue Routes

The syntax for creating and deleting queue routes is as follows:

        qpid-route [OPTIONS] queue add <dest-broker> <src-broker> <dest-exchange> <src-queue>
        qpid-route [OPTIONS] queue del <dest-broker> <src-broker> <dest-exchange> <src-queue>
          

For instance, the following creates a queue route that routes all
messages from the queue named `public` on the source broker
`localhost:10002` to the `amq.fanout` exchange on the destination broker
`localhost:10001`:

        $ qpid-route queue add localhost:10001 localhost:10002 amq.fanout public
          

If the `-d` option is specified, this queue route is persistent, and
will be restored if one or both of the brokers is restarted:

        $ qpid-route -d queue add localhost:10001 localhost:10002 amq.fanout public
          

The `del` command takes the same arguments as the `add` command. The
following command deletes the queue route described above:

        $ qpid-route queue del localhost:10001 localhost:10002 amq.fanout public
          

### <span class="header-section-number">1.4.2</span> Creating and Deleting Exchange Routes

The syntax for creating and deleting exchange routes is as follows:

        qpid-route [OPTIONS] route add <dest-broker> <src-broker> <exchange> <routing-key>
        qpid-route [OPTIONS] route del <dest-broker> <src-broker> <exchange> <routing-key>
        qpid-route [OPTIONS] flush [<broker>]
          

For instance, the following creates an exchange route that routes
messages that match the binding key `global.#` from the `amq.topic`
exchange on the source broker `localhost:10002` to the `amq.topic`
exchange on the destination broker `localhost:10001`:

        $ qpid-route route add localhost:10001 localhost:10002 amq.topic global.#
          

In many applications, messages published to the destination exchange
should also be routed to the source exchange. This is accomplished by
creating a second exchange route, reversing the roles of the two
exchanges:

        $ qpid-route route add localhost:10002 localhost:10001 amq.topic global.#
          

If the `-d` option is specified, the exchange route is persistent, and
will be restored if one or both of the brokers is restarted:

        $ qpid-route -d route add localhost:10001 localhost:10002 amq.fanout public
          

The `del` command takes the same arguments as the `add` command. The
following command deletes the first exchange route described above:

        $ qpid-route route del localhost:10001 localhost:10002 amq.topic global.#
          

### <span class="header-section-number">1.4.3</span> Deleting all routes for a broker

Use the `flush` command to delete all routes for a given broker:

        qpid-route [OPTIONS] flush [<broker>]
          

For instance, the following command deletes all routes for the broker
`localhost:10001`:

        $ qpid-route flush localhost:10001
          

### <span class="header-section-number">1.4.4</span> Creating and Deleting Dynamic Exchange Routes

The syntax for creating and deleting dynamic exchange routes is as
follows:

        qpid-route [OPTIONS] dynamic add <dest-broker> <src-broker> <exchange>
        qpid-route [OPTIONS] dynamic del <dest-broker> <src-broker> <exchange>
          

In the following examples, we will route messages from a topic exchange.
We will create a new topic exchange and federate it so that we are not
affected by other all clients that use the built-in `amq.topic`
exchange. The following commands create a new topic exchange on each of
two brokers:

        $ qpid-config -a localhost:10003 add exchange topic fed.topic
        $ qpid-config -a localhost:10004 add exchange topic fed.topic
          

Now let's create a dynamic exchange route that routes messages from the
`fed.topic` exchange on the source broker `localhost:10004` to the
`fed.topic` exchange on the destination broker `localhost:10003` if they
match any binding on the destination broker's `fed.topic` exchange:

        $ qpid-route dynamic add localhost:10003 localhost:10004 fed.topic
          

Internally, this creates a private autodelete queue on the source
broker, and binds that queue to the `fed.topic` exchange on the source
broker, using each binding associated with the `fed.topic` exchange on
the destination broker.

In many applications, messages published to the destination exchange
should also be routed to the source exchange. This is accomplished by
creating a second dynamic exchange route, reversing the roles of the two
exchanges:

        $ qpid-route dynamic add localhost:10004 localhost:10003 fed.topic
          

If the `-d` option is specified, the exchange route is persistent, and
will be restored if one or both of the brokers is restarted:

        $ qpid-route -d dynamic add localhost:10004 localhost:10003 fed.topic
          

When an exchange route is durable, the private queue used to store
messages for the route on the source exchange is also durable. If the
connection between the brokers is lost, messages for the destination
exchange continue to accumulate until it can be restored.

The `del` command takes the same arguments as the `add` command. The
following command deletes the first exchange route described above:

        $ qpid-route dynamic del localhost:10004 localhost:10003 fed.topic
          

Internally, this deletes the bindings on the source exchange for the the
private queues associated with the message route.

### <span class="header-section-number">1.4.5</span> Viewing Routes

The `route list` command shows the routes associated with an individual
broker. For instance, suppose we have created the following two routes:

        $ qpid-route dynamic add localhost:10003 localhost:10004 fed.topic
        $ qpid-route dynamic add localhost:10004 localhost:10003 fed.topic
          

We can now use `route list` to show all routes for the broker
`localhost:10003`:

        $ qpid-route route list localhost:10003
        localhost:10003 localhost:10004 fed.topic <dynamic>
          

Note that this shows only one of the two routes we created, the route
for which `localhost:10003` is a destination. If we want to see the
route for which `localhost:10004` is a destination, we need to do
another route list:

        $ qpid-route route list localhost:10004
        localhost:10004 localhost:10003 fed.topic <dynamic>
          

The `route map` command shows all routes associated with a broker, and
recursively displays all routes for brokers involved in federation
relationships with the given broker. For instance, here is the output
for the two brokers configured above:

        $ qpid-route route map localhost:10003

        Finding Linked Brokers:
        localhost:10003... Ok
        localhost:10004... Ok

        Dynamic Routes:

        Exchange fed.topic:
        localhost:10004 <=> localhost:10003

        Static Routes:
        none found
          

Note that the two dynamic exchange links are displayed as though they
were one bidirectional link. The `route map` command is particularly
helpful for larger, more complex networks. Let's configure a somewhat
more complex network with 16 dynamic exchange routes:

        qpid-route dynamic add localhost:10001 localhost:10002 fed.topic
        qpid-route dynamic add localhost:10002 localhost:10001 fed.topic

        qpid-route dynamic add localhost:10003 localhost:10002 fed.topic
        qpid-route dynamic add localhost:10002 localhost:10003 fed.topic

        qpid-route dynamic add localhost:10004 localhost:10002 fed.topic
        qpid-route dynamic add localhost:10002 localhost:10004 fed.topic

        qpid-route dynamic add localhost:10002 localhost:10005 fed.topic
        qpid-route dynamic add localhost:10005 localhost:10002 fed.topic

        qpid-route dynamic add localhost:10005 localhost:10006 fed.topic
        qpid-route dynamic add localhost:10006 localhost:10005 fed.topic

        qpid-route dynamic add localhost:10006 localhost:10007 fed.topic
        qpid-route dynamic add localhost:10007 localhost:10006 fed.topic

        qpid-route dynamic add localhost:10006 localhost:10008 fed.topic
        qpid-route dynamic add localhost:10008 localhost:10006 fed.topic
          

Now we can use `route map` starting with any one broker, and see the
entire network:

        $ ./qpid-route route map localhost:10001

        Finding Linked Brokers:
        localhost:10001... Ok
        localhost:10002... Ok
        localhost:10003... Ok
        localhost:10004... Ok
        localhost:10005... Ok
        localhost:10006... Ok
        localhost:10007... Ok
        localhost:10008... Ok

        Dynamic Routes:

        Exchange fed.topic:
        localhost:10002 <=> localhost:10001
        localhost:10003 <=> localhost:10002
        localhost:10004 <=> localhost:10002
        localhost:10005 <=> localhost:10002
        localhost:10006 <=> localhost:10005
        localhost:10007 <=> localhost:10006
        localhost:10008 <=> localhost:10006

        Static Routes:
        none found
          

### <span class="header-section-number">1.4.6</span> Resilient Connections

When a broker route is created, or when a durable broker route is
restored after broker restart, a connection is created between the
source broker and the destination broker. The connections used between
brokers are called resilient connections; if the connection fails due to
a communication error, it attempts to reconnect. The retry interval
begins at 2 seconds and, as more attempts are made, grows to 64 seconds,
and continues to retry every 64 seconds thereafter. If the connection
fails due to an authentication problem, it will not continue to retry.

The command `list connections` can be used to show the resilient
connections for a broker:

        $ qpid-route list connections localhost:10001

        Host            Port    Transport Durable  State             Last Error
        =============================================================================
        localhost       10002   tcp          N     Operational
        localhost       10003   tcp          N     Operational
        localhost       10009   tcp          N     Waiting           Connection refused
          

In the above output, `Last Error` contains the string representation of
the last connection error received for the connection. `State`
represents the state of the connection, and may be one of the following
values:

|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Waiting     | Waiting before attempting to reconnect.                                                                                                                            |
| Connecting  | Attempting to establish the connection.                                                                                                                            |
| Operational | The connection has been established and can be used.                                                                                                               |
| Failed      | The connection failed and will not retry (usually because authentication failed).                                                                                  |
| Closed      | The connection has been closed and will soon be deleted.                                                                                                           |
| Passive     | If a cluster is federated to another cluster, only one of the nodes has an actual connection to remote node. Other nodes in the cluster have a passive connection. |

## <span class="header-section-number">1.5</span> Broker options affecting federation

The following broker options affect federation:

Broker Options for Federation

Options for Federation

`federation-tag NAME`

A unique name to identify this broker in federation network. If not
specified, the broker will generate a unique identifier.

`link-maintenance-interval SECONDS`

Interval to check if links need to be re-connected. Default 2 seconds.
Can be a sub-second interval for faster failover, e.g. 0.1 seconds.

`link-heartbeat-interval SECONDS`

Heart-beat interval for federation links. If no heart-beat is received
for twice the interval the link is considered dead. Default 120 seconds.
