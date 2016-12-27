# <span class="header-section-number">1</span> High Availability

# <span class="header-section-number">2</span> General Introduction

The term High Availability (HA) usually refers to having a number of
instances of a service such as a Message Broker available so that should
a service unexpectedly fail, or requires to be shutdown for maintenance,
users may quickly connect to another instance and continue their work
with minimal interruption. HA is one way to make a overall system more
resilient by eliminating a single point of failure from a system.

HA offerings are usually categorised as **Active/Active** or
**Active/Passive**. An Active/Active system is one where all nodes
within the group are usually available for use by clients all of the
time. In an Active/Passive system, one only node within the group is
available for use by clients at any one time, whilst the others are in
some kind of standby state, awaiting to quickly step-in in the event the
active node becomes unavailable.

# <span class="header-section-number">3</span> Overview of HA within the Java Broker

The Java Broker provides a HA implementation offering an
**Active/Passive** mode of operation. When using HA, many instances of
the Java Broker work together to form an high availability group of two
or more nodes.

The remainder of this section now talks about the specifics of how HA is
achieved in terms of the [concepts](#Java-Broker-Concepts) introduced
earlier in this book.

The [Virtualhost](#Java-Broker-Concepts-Virtualhosts) is the unit of
replication. This means that any *durable* queues, exchanges, and
bindings belonging to that virtualhost, any *persistent* messages
contained within the queues and any attribute settings applied to the
virtualhost itself are automatically replicated to all nodes within the
group.<span id="fnref1">[^1^](#fn1)</span>

It is the [Virtualhost Nodes](#Java-Broker-Concepts-Virtualhost-Nodes)
(from different Broker instances) that join together to form a group.
The virtualhost nodes collectively to coordinate the group: they
organise replication between the master and replicas and conduct
elections to determine who becomes the new master in the event of the
old failing.

When a virtualhost node is in the *master* role, the virtualhost beneath
it is available for messaging work. Any write operations sent to the
virtualhost are automatically replicated to all other nodes in group.

When a virtualhost node is in the *replica* role, the virtualhost
beneath it is always unavailable for message work. Any attempted
connections to a virtualhost in this state are automatically turned
away, allowing a messaging client to discover where the master currently
resides. When in replica role, the node sole responsibility is to
consume a replication stream in order that it remains up to date with
the master.

Messaging clients discover the active virtualhost.This can be achieved
using a static technique (for instance, a failover url (a feature of a
Qpid Java Client)), or a dynamic one utilising some kind of proxy or
virtual IP (VIP).

The figure that follows illustrates a group formed of three virtualhost
nodes from three separate Broker instances. A client is connected to the
virtualhost node that is in the master role. The two virtualhost nodes
`weather1` and `weather3` are replicas and are receiving a stream of
updates.

![ Diagram showing a 3 node group deployed across three Brokers
](images/HA-Overview.png)

Currently, the only virtualhost/virtualhost node type offering HA is BDB
HA. Internally, this leverages the HA capabilities of the Berkeley DB JE
edition. BDB JE is an [optional
dependency](#Java-Broker-Miscellaneous-Installing-Oracle-BDB-JE) of the
Broker.

> **Note**
>
> The Java Broker HA solution is incompatible with the HA solution
> offered by the CPP Broker. It is not possible to co-locate Java and
> CPP Brokers within the same group.

# <span class="header-section-number">4</span> Creating a group

This section describes how to create a group. At a high level, creating
a group involves first creating the first node standalone, then creating
subsequent nodes referencing the first node so the nodes can introduce
themselves and gradually the group is built up.

A group is created through either [Web
Management](#Java-Broker-Management-Channel-Web-Console) or the [REST
API](#Java-Broker-Management-Channel-REST-API). These instructions
presume you are using Web Management. To illustrate the example it
builds the group illustrated in figure ?

1.  Install a Broker on each machine that will be used to host the
    group. As messaging clients will need to be able to connect to and
    authentication to all Brokers, it usually makes sense to choose a
    common authentication mechanism e.g. Simple LDAP Authentication,
    External with SSL client authentication or Kerberos.

2.  Select one Broker instance to host the first node instance. This
    choice is an arbitrary one. The node is special only whilst creating
    group. Once creation is complete, all nodes will be considered
    equal.

3.  Click the `Add` button on the Virtualhost Panel on the Broker tab.

    1.  Give the Virtualhost node a unique name e.g. `weather1`. The
        name must be unique within the group and unique to that Broker.
        It is best if the node names are chosen from a different
        nomenclature than the machine names themselves.

    2.  Choose `BDB_HA` and select `New group`

    3.  Give the group a name e.g. `weather`. The group name must be
        unique and will be the name also given to the virtualhost, so
        this is the name the messaging clients will use in their
        connection url.

    4.  Give the address of this node. This is an address on this node's
        host that will be used for replication purposes. The hostname
        *must* be resolvable by all the other nodes in the group. This
        is separate from the address used by messaging clients to
        connect to the Broker. It is usually best to choose a symbolic
        name, rather than an IP address.

    5.  Now add the node addresses of all the other nodes that will form
        the group. In our example we are building a three node group so
        we give the node addresses of `chaac:5000` and `indra:5000`.

    6.  Click Add to create the node. The virtualhost node will be
        created with the virtualhost. As there is only one node at this
        stage, the role will be master.

    Creating 1st node in a group

4.  Now move to the second Broker to be the group. Click the `Add`
    button on the Virtualhost Panel on the Broker tab of the second
    Broker.

    1.  Give the Virtualhost node a unique name e.g. `weather2`.

    2.  Choose `BDB_HA` and choose `Existing group`

    3.  Give the details of the *existing node*. Following our example,
        specify `weather`, `weather1` and `thor:5000`

    4.  Give the address of this node.

    5.  Click Add to create the node. The node will use the existing
        details to contact it and introduce itself into the group. At
        this stage, the group will have two nodes, with the second node
        in the replica role.

    6.  Repeat these steps until you have added all the nodes to the
        group.

    Adding subsequent nodes to the group

The group is now formed and is ready for us. Looking at the virtualhost
node of any of the nodes shows a complete view of the whole group. View
of group from one node

# <span class="header-section-number">5</span> Behaviour of the Group

This section first describes the behaviour of the group in its default
configuration. It then goes on to talk about the various controls that
are available to override it. It describes the controls available that
affect the [durability](http://en.wikipedia.org/wiki/ACID#Durability) of
transactions and the data consistency between the master and replicas
and thus make trade offs between performance and reliability.

## <span class="header-section-number">5.1</span> Default Behaviour

Let's first look at the behaviour of a group in default configuration.

In the default configuration, for any messaging work to be done, there
must be at least *quorum* nodes present. This means for example, in a
three node group, this means there must be at least two nodes available.

When a messaging client sends a transaction, it can be assured that,
before the control returns back to his application after the commit call
that the following is true:

-   At the master, the transaction is *written to disk and OS level
    caches are flushed* meaning the data is on the storage device.

-   At least quorum minus 1 replicas, *acknowledge the receipt of
    transaction*. The replicas will write the data to the storage device
    sometime later.

If there were to be a master failure immediately after the transaction
was committed, the transaction would be held by at least quorum minus
one replicas. For example, if we had a group of three, then we would be
assured that at least one replica held the transaction.

In the event of a master failure, if quorum nodes remain, those nodes
hold an election. The nodes will elect master the node with the most
recent transaction. If two or more nodes have the most recent
transaction the group makes an arbitrary choice. If quorum number of
nodes does not remain, the nodes cannot elect a new master and will wait
until nodes rejoin. You will see later that manual controls are
available allow service to be restored from fewer than quorum nodes and
to influence which node gets elected in the event of a tie.

Whenever a group has fewer than quorum nodes present, the virtualhost
will be unavailable and messaging connections will be refused. If quorum
disappears at the very moment a messaging client sends a transaction
that transaction will fail.

You will have noticed the difference in the synchronization policies
applied the master and the replicas. The replicas send the
acknowledgement back before the data is written to disk. The master
synchronously writes the transaction to storage. This is an example of a
trade off between durability and performance. We will see more about how
to control this trade off later.

## <span class="header-section-number">5.2</span> Synchronization Policy

The *synchronization policy* dictates what a node must do when it
receives a transaction before it acknowledges that transaction to the
rest of the group.

The following options are available:

-   *SYNC*. The node must write the transaction to disk and flush any OS
    level buffers before sending the acknowledgement. SYNC is offers the
    highest durability but offers the least performance.

-   *WRITE\_NO\_SYNC*. The node must write the transaction to disk
    before sending the acknowledgement. OS level buffers will be flush
    as some point later. This typically provides an assurance against
    failure of the application but not the operating system or hardware.

-   *NO\_SYNC*. The node immediately sends the acknowledgement. The
    transaction will be written and OS level buffers flushed as some
    point later. NO\_SYNC offers the highest performance but the lowest
    durability level. This synchronization policy is sometimes known as
    *commit to the network*.

It is possible to assign a one policy to the master and a different
policy to the replicas. These are configured as [attributes on the
virtualhost](#Java-Broker-Management-Managing-Virtualhost-Attributes).
By default the master uses *SYNC* and replicas use *NO\_SYNC*.

## <span class="header-section-number">5.3</span> Node Priority

Node priority can be used to influence the behaviour of the election
algorithm. It is useful in the case were you want to favour some nodes
over others. For instance, if you wish to favour nodes located in a
particular data centre over those in a remote site.

The following options are available:

-   *Highest*. Nodes with this priority will be more favoured. In the
    event of two or more nodes having the most recent transaction, the
    node with this priority will be elected master. If two or more nodes
    have this priority the algorithm will make an arbitrary choice.

-   *High*. Nodes with this priority will be favoured but not as much so
    as those with Highest.

-   *Normal*. This is default election priority.

-   *Never*. The node will never be elected *even if the node has the
    most recent transaction*. The node will still keep up to date with
    the replication stream and will still vote itself, but can just
    never be elected.

Node priority is configured as an [attribute on the virtualhost
node](#Java-Broker-Management-Managing-Virtualhost-Nodes-Attributes) and
can be changed at runtime and is effective immediately.

> **Important**
>
> Use of the Never priority can lead to transaction loss. For example,
> consider a group of three where replica-2 is marked as Never. If a
> transaction were to arrive and it be acknowledged only by Master and
> Replica-2, the transaction would succeed. Replica 1 is running behind
> for some reason (perhaps a full-GC). If a Master failure were to occur
> at that moment, the replicas would elect Replica-1 even though
> Replica-2 had the most recent transaction.
>
> Transaction loss is reported by message
> [HA-1014](#Java-Broker-Appendix-Operation-Logging-Message-HA-1014).

## <span class="header-section-number">5.4</span> Required Minimum Number Of Nodes

This controls the required minimum number of nodes to complete a
transaction and to elect a new master. By default, the required number
of nodes is set to *Default* (which signifies quorum).

It is possible to reduce the required minimum number of nodes. The
rationale for doing this is normally to temporarily restore service from
fewer than quorum nodes following an extraordinary failure.

For example, consider a group of three. If one node were to fail, as
quorum still remained, the system would continue work without any
intervention. If the failing node were the master, a new master would be
elected.

What if a further node were to fail? Quorum no longer remains, and the
remaining node would just wait. It cannot elect itself master. What if
we wanted to restore service from just this one node?

In this case, Required Number of Nodes can be reduced to 1 on the remain
node, allowing the node to elect itself and service to be restored from
the singleton. Required minimum number of nodes is configured as an
[attribute on the virtualhost
node](#Java-Broker-Management-Managing-Virtualhost-Nodes-Attributes) and
can be changed at runtime and is effective immediately.

> **Important**
>
> The attribute must be used cautiously. Careless use will lead to lost
> transactions and can lead to a
> [split-brain](http://en.wikipedia.org/wiki/Split-brain_(computing)) in
> the event of a network partition. If used to temporarily restore
> service from fewer than quorum nodes, it is *imperative* to revert it
> to the Default value as the failed nodes are restored.
>
> Transaction loss is reported by message
> [HA-1014](#Java-Broker-Appendix-Operation-Logging-Message-HA-1014).

## <span class="header-section-number">5.5</span> Designated Primary

This attribute applies to the groups of two only.

In a group of two, if a node were to fail then in default configuration
work will cease as quorum no longer exists. A single node cannot elect
itself master.

The designated primary flag allows a node in a two node group to elect
itself master and to operate sole. Designated Primary is configured as
an [attribute on the virtualhost
node](#Java-Broker-Management-Managing-Virtualhost-Nodes-Attributes) and
can be changed at runtime and is effective immediately.

For example, consider a group of two where the master fails. Service
will be interrupted as the remaining node cannot elect itself master. To
allow it to become master, apply the designated primary flag to it. It
will elect itself master and work can continue, albeit from one node.

> **Important**
>
> It is imperative not to allow designated primary to be set on both
> nodes at once. To do so will mean, in the event of a network
> partition, a
> [split-brain](http://en.wikipedia.org/wiki/Split-brain_(computing))
> will occur.
>
> Transaction loss is reported by message
> [HA-1014](#Java-Broker-Appendix-Operation-Logging-Message-HA-1014).

# <span class="header-section-number">6</span> Node Operations

## <span class="header-section-number">6.1</span> Lifecycle

Virtualhost nodes can be stopped, started and deleted.

-   *Stop*

    Stopping a master node will cause the node to temporarily leave the
    group. Any messaging clients will be disconnected and any in-flight
    transaction rollbacked. The remaining nodes will elect a new master
    if quorum number of nodes still remains.

    Stopping a replica node will cause the node to temporarily leave the
    group too. Providing quorum still exists, the current master will
    continue without interruption. If by leaving the group, quorum no
    longer exists, all the nodes will begin waiting, disconnecting any
    messaging clients, and the virtualhost will become unavailable.

    A stopped virtualhost node is still considered to be a member of the
    group.

-   *Start*

    Starting a virtualhost node allows it to rejoin the group.

    If the group already has a master, the node will catch up from the
    master and then become a replica once it has done so.

    If the group did not have quorum and so had no master, but the
    rejoining of this node means quorum now exists, an election will
    take place. The node with the most up to date transaction will
    become master unless influenced by the priority rules described
    above.

    > **Note**
    >
    > The length of time taken to catch up will depend on how long the
    > node has been stopped. The worst case is where the node has been
    > stopped for more than one hour. In this case, the master will
    > perform an automated `network restore`. This involves streaming
    > all the data held by the master over to the replica. This could
    > take considerable time.

-   *Delete*

    A virtualhost node can be deleted. Deleting a node permanently
    removes the node from the group. The data stored locally is removed
    but this does not affect the data held by the remainder of the
    group.

    > **Note**
    >
    > The names of deleted virtualhost node cannot be reused within a
    > group.

It is also possible to add nodes to an existing group using the
procedure described above.

## <span class="header-section-number">6.2</span> Transfer Master

This operation allows the mastership to be moved from node to node. This
is useful for restoring a business as usual state after a failure.

When using this function, the following occurs.

1.  The system first gives time for the chosen new master to become
    reasonable up to date.

2.  It then suspends transactions on the old master and allows the
    chosen node to become up to date.

3.  The suspended transactions are aborted and any messaging clients
    connected to the old master are disconnected.

4.  The chosen master becomes the new master. The old master becomes a
    replica.

5.  Messaging clients reconnect the new master.

# <span class="header-section-number">7</span> Client failover

As mentioned above, the clients need to be able to find the location of
the active virtualhost within the group.

Clients can do this using a static technique, for example , utilising
the [failover feature of the Qpid connection
url](&qpidjmsdocClientConectionUrl;) where the client has a list of all
the nodes, and tries each node in sequence until it discovers the node
with the active virtualhost.

Another possibility is a dynamic technique utilising a proxy or Virtual
IP (VIP). These require other software and/or hardware and are outside
the scope of this document.

# <span class="header-section-number">8</span> Qpid JMX API for HA

The Qpid JMX API for HA is now deprecated. New users are recommended to
use the [REST API.](#Java-Broker-Management-Channel-REST-API)

# <span class="header-section-number">9</span> Disk space requirements

In the case where node in a group are down, the master must keep the
data they are missing for them to allow them to return to the replica
role quickly.

By default, the master will retain up to 1hour of missed transactions.
In a busy production system, the disk space occupied could be
considerable.

This setting is controlled by virtualhost context variable
`je.rep.repStreamTimeout`.

# <span class="header-section-number">10</span> Network Requirements

The HA Cluster performance depends on the network bandwidth, its use by
existing traffic, and quality of service.

In order to achieve the best performance it is recommended to use a
separate network infrastructure for the Qpid HA Nodes which might
include installation of dedicated network hardware on Broker hosts,
assigning a higher priority to replication ports, installing a group in
a separate network not impacted by any other traffic.

# <span class="header-section-number">11</span> Security

The replication stream between the master and the replicas is insecure
and can be intercepted by anyone having access to the replication
network.

In order to reduce the security risks the entire HA group is recommended
to run in a separate network protected from general access and/or
utilise SSH-tunnels/IPsec.

# <span class="header-section-number">12</span> Backups

It is recommend to use the hot backup script to periodically backup
every node in the group. ?.

# <span class="header-section-number">13</span> Reset Group Information

BDB JE internally stores details of the group within its database. There
are some circumstances when resetting this information is useful.

-   Copying data between environments (e.g. production to UAT)

-   Some disaster recovery situations where a group must be recreated on
    new hardware

This is not an normal operation and is not usually required

The following command replaces the group table contained within the JE
logs files with the provided information.

java -cp je-ORACLEBDBPRODUCTVERSION.jar
com.sleepycat.je.rep.util.DbResetRepGroup -h
path/to/jelogfiles -groupName newgroupname -nodeName
newnodename -nodeHostPort newhostname:5000

The modified log files can then by copied into
`${QPID_WORK}/<nodename>/config` directory of a target Broker. Then
start the Broker, and add a BDB HA Virtualhost node specify the same
group name, node name and node address. You will then have a group with
a single node, ready to start re-adding additional nodes as described
above.

------------------------------------------------------------------------

1.  <div id="fn1">

    </div>

    Transient messages and messages on non-durable queues are not
    replicated.[↩](#fnref1)


