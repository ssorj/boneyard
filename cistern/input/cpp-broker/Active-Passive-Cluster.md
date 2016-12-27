# <span class="header-section-number">1</span> Active-Passive Messaging Clusters

## <span class="header-section-number">1.1</span> Overview

The High Availability (HA) module provides active-passive, hot-standby
messaging clusters to provide fault tolerant message delivery.

In an active-passive cluster only one broker, known as the primary, is
active and serving clients at a time. The other brokers are standing by
as backups. Changes on the primary are replicated to all the backups so
they are always up-to-date or "hot". Backup brokers reject client
connection attempts, to enforce the requirement that clients only
connect to the primary.

If the primary fails, one of the backups is promoted to take over as the
new primary. Clients fail-over to the new primary automatically. If
there are multiple backups, the other backups also fail-over to become
backups of the new primary.

This approach relies on an external cluster resource manager to detect
failures, choose the new primary and handle network partitions.
[rgmanager](https://fedorahosted.org/cluster/wiki/RGManager) is
supported initially, but others may be supported in the future.

### <span class="header-section-number">1.1.1</span> Avoiding message loss

In order to avoid message loss, the primary broker *delays
acknowledgement* of messages received from clients until the message has
been replicated and acknowledged by all of the back-up brokers, or has
been consumed from the primary queue.

This ensures that all acknowledged messages are safe: they have either
been consumed or backed up to all backup brokers. Messages that are
consumed *before* they are replicated do not need to be replicated. This
reduces the work load when replicating a queue with active consumers.

Clients keep *unacknowledged* messages in a buffer <span
id="fnref1">[^1^](#fn1)</span> until they are acknowledged by the
primary. If the primary fails, clients will fail-over to the new primary
and *re-send* all their unacknowledged messages. <span
id="fnref2">[^2^](#fn2)</span>

If the primary crashes, all the *acknowledged* messages will be
available on the backup that takes over as the new primary. The
*unacknowledged* messages will be re-sent by the clients. Thus no
messages are lost.

Note that this means it is possible for messages to be *duplicated*. In
the event of a failure it is possible for a message to received by the
backup that becomes the new primary *and* re-sent by the client. The
application must take steps to identify and eliminate duplicates.

When a new primary is promoted after a fail-over it is initially in
"recovering" mode. In this mode, it delays acknowledgement of messages
on behalf of all the backups that were connected to the previous
primary. This protects those messages against a failure of the new
primary until the backups have a chance to connect and catch up.

Not all messages need to be replicated to the back-up brokers. If a
message is consumed and acknowledged by a regular client before it has
been replicated to a backup, then it doesn't need to be replicated.

Stand-alone  
Broker is not part of a HA cluster.

Joining  
Newly started broker, not yet connected to any existing primary.

Catch-up  
A backup broker that is connected to the primary and downloading
existing state (queues, messages etc.)

Ready  
A backup broker that is fully caught-up and ready to take over as
primary.

Recovering  
Newly-promoted primary, waiting for backups to connect and catch up.
Clients can connect but they are stalled until the primary is active.

Active  
The active primary broker with all backups connected and caught-up.

### <span class="header-section-number">1.1.2</span> Limitations

There are a some known limitations in the current implementation. These
will be fixed in future versions.

-   Transactional changes to queue state are not replicated atomically.
    If the primary crashes during a transaction, it is possible that the
    backup could contain only part of the changes introduced by a
    transaction.

-   Configuration changes (creating or deleting queues, exchanges and
    bindings) are replicated asynchronously. Management tools used to
    make changes will consider the change complete when it is complete
    on the primary, it may not yet be replicated to all the backups.

-   Federation links *to* the primary will fail over correctly.
    Federated links *from* the primary will be lost in fail over, they
    will not be re-connected to the new primary. It is possible to work
    around this by replacing the `qpidd-primary` start up script with a
    script that re-creates federation links when the primary is
    promoted.

## <span class="header-section-number">1.2</span> Virtual IP Addresses

Some resource managers (including `rgmanager`) support virtual IP
addresses. A virtual IP address is an IP address that can be relocated
to any of the nodes in a cluster. The resource manager associates this
address with the primary node in the cluster, and relocates it to the
new primary when there is a failure. This simplifies configuration as
you can publish a single IP address rather than a list.

A virtual IP address can be used by clients to connect to the primary.
The following sections will explain how to configure virtual IP
addresses for clients or brokers.

## <span class="header-section-number">1.3</span> Configuring the Brokers

The broker must load the `ha` module, it is loaded by default. The
following broker options are available for the HA module.

> **Note**
>
> Broker management is required for HA to operate, it is enabled by
> default. The option `mgmt-enable` must not be set to "no"

> **Note**
>
> Incorrect security settings are a common cause of problems when
> getting started, see ?.

Broker Options for High Availability Messaging Cluster

Options for High Availability Messaging Cluster

`ha-cluster yes|no`

Set to "yes" to have the broker join a cluster.

`ha-queue-replication yes|no`

Enable replication of specific queues without joining a cluster, see ?.

`ha-brokers-url URL`

The URL <span id="fnref3">[^3^](#fn3)</span> used by cluster brokers to
connect to each other. The URL should contain a comma separated list of
the broker addresses, rather than a virtual IP address.

`ha-public-url URL`

This option is only needed for backwards compatibility if you have been
using the `amq.failover` exchange. This exchange is now obsolete, it is
recommended to use a virtual IP address instead.

If set, this URL is advertised by the `amq.failover` exchange and
overrides the broker option `known-hosts-url`

`ha-replicate `VALUE

Specifies whether queues and exchanges are replicated by default. VALUE
is one of: `none`, `configuration`, `all`. For details see ?.

`ha-username USER`

`ha-password PASS`

`ha-mechanism MECHANISM`

Authentication settings used by HA brokers to connect to each other, see
?

`ha-backup-timeoutSECONDS` <span id="fnref4">[^4^](#fn4)</span>

Maximum time that a recovering primary will wait for an expected backup
to connect and become ready.

`link-maintenance-interval SECONDS`

HA uses federation links to connect from backup to primary. Backup
brokers check the link to the primary on this interval and re-connect if
need be. Default 2 seconds. Set lower for faster failover, e.g. 0.1
seconds. Setting too low will result in excessive link-checking on the
backups.

`link-heartbeat-interval SECONDS`

HA uses federation links to connect from backup to primary. If no
heart-beat is received for twice this interval the primary will consider
that backup dead (e.g. if backup is hung or partitioned.) This interval
is also used to time-out for broker status checks, it may take up to
this interval for rgmanager to detect a hung or partitioned broker.
Clients sending messages may be held up during this time. Default 120
seconds: you will probably want to set this to a lower value e.g. 10. If
set too low rgmanager may consider a slow broker to have failed and kill
it.

To configure a HA cluster you must set at least `ha-cluster` and
`ha-brokers-url`.

## <span class="header-section-number">1.4</span> The Cluster Resource Manager

Broker fail-over is managed by a cluster resource manager. An
integration with
[rgmanager](https://fedorahosted.org/cluster/wiki/RGManager) is
provided, but it is possible to integrate with other resource managers.

The resource manager is responsible for starting the `qpidd` broker on
each node in the cluster. The resource manager then promotes one of the
brokers to be the primary. The other brokers connect to the primary as
backups, using the URL provided in the `ha-brokers-url` configuration
option.

Once connected, the backup brokers synchronize their state with the
primary. When a backup is synchronized, or "hot", it is ready to take
over if the primary fails. Backup brokers continually receive updates
from the primary in order to stay synchronized.

If the primary fails, backup brokers go into fail-over mode. The
resource manager must detect the failure and promote one of the backups
to be the new primary. The other backups connect to the new primary and
synchronize their state with it.

The resource manager is also responsible for protecting the cluster from
split-brain conditions resulting from a network partition. A network
partition divide a cluster into two sub-groups which cannot see each
other. Usually a quorum voting algorithm is used that disables nodes in
the inquorate sub-group.

## <span class="header-section-number">1.5</span> Configuring with `rgmanager` as resource manager

This section assumes that you are already familiar with setting up and
configuring clustered services using `cman` and `rgmanager`. It will
show you how to configure an active-passive, hot-standby `qpidd` HA
cluster with `rgmanager`.

> **Note**
>
> Once all components are installed it is important to take the
> following step:
>
>     chkconfig rgmanager on
>     chkconfig cman on
>     chkconfig qpidd off
>         
>
> The qpidd service must be *off* in `chkconfig` because `rgmanager`
> will start and stop `qpidd`. If the normal system init process also
> attempts to start and stop qpidd it can cause rgmanager to lose track
> of qpidd processes. The symptom when this happens is that `clustat`
> shows a `qpidd` service to be stopped when in fact there is a `qpidd`
> process running. The `qpidd` log will show errors like this:
>
>     critical Unexpected error: Daemon startup failed: Cannot lock /var/lib/qpidd/lock: Resource temporarily unavailable
>         

You must provide a `cluster.conf` file to configure `cman` and
`rgmanager`. Here is an example `cluster.conf` file for a cluster of 3
nodes named node1, node2 and node3. We will go through the configuration
step-by-step.

          
    <?xml version="1.0"?>
    <!--
    This is an example of a cluster.conf file to run qpidd HA under rgmanager.
    This example assumes a 3 node cluster, with nodes named node1, node2 and node3.

    NOTE: fencing is not shown, you must configure fencing appropriately for your cluster.
    -->

    <cluster name="qpid-test" config_version="18">
      <!-- The cluster has 3 nodes. Each has a unique nodeid and one vote
           for quorum. -->
      <clusternodes>
        <clusternode name="node1.example.com" nodeid="1"/>
        <clusternode name="node2.example.com" nodeid="2"/>
        <clusternode name="node3.example.com" nodeid="3"/>
      </clusternodes>

      <!-- Resouce Manager configuration. -->

       status_poll_interval is the interval in seconds that the resource manager checks the status
       of managed services. This affects how quickly the manager will detect failed services.
       -->
      <rm status_poll_interval="1">
        <!--
        There is a failoverdomain for each node containing just that node.
        This lets us stipulate that the qpidd service should always run on each node.
        -->
        <failoverdomains>
          <failoverdomain name="node1-domain" restricted="1">
        <failoverdomainnode name="node1.example.com"/>
          </failoverdomain>
          <failoverdomain name="node2-domain" restricted="1">
        <failoverdomainnode name="node2.example.com"/>
          </failoverdomain>
          <failoverdomain name="node3-domain" restricted="1">
        <failoverdomainnode name="node3.example.com"/>
          </failoverdomain>
        </failoverdomains>

        <resources>
          <!-- This script starts a qpidd broker acting as a backup. -->
          <script file="/etc/init.d/qpidd" name="qpidd"/>

          <!-- This script promotes the qpidd broker on this node to primary. -->
          <script file="/etc/init.d/qpidd-primary" name="qpidd-primary"/>

          <!--
              This is a virtual IP address for client traffic.
          monitor_link="yes" means monitor the health of the NIC used for the VIP.
          sleeptime="0" means don't delay when failing over the VIP to a new address.
          -->
          <ip address="20.0.20.200" monitor_link="yes" sleeptime="0"/>
        </resources>

        <!-- There is a qpidd service on each node, it should be restarted if it fails. -->
        <service name="node1-qpidd-service" domain="node1-domain" recovery="restart">
          <script ref="qpidd"/>
        </service>
        <service name="node2-qpidd-service" domain="node2-domain" recovery="restart">
          <script ref="qpidd"/>
        </service>
        <service name="node3-qpidd-service" domain="node3-domain"  recovery="restart">
          <script ref="qpidd"/>
        </service>

        <!-- There should always be a single qpidd-primary service, it can run on any node. -->
        <service name="qpidd-primary-service" autostart="1" exclusive="0" recovery="relocate">
          <script ref="qpidd-primary"/>
          <!-- The primary has the IP addresses for brokers and clients to connect. -->
          <ip ref="20.0.20.200"/>
        </service>
      </rm>
    </cluster>
          
        

There is a `failoverdomain` for each node containing just that one node.
This lets us stipulate that the qpidd service should always run on all
nodes.

The `resources` section defines the `qpidd` script used to start the
`qpidd` service. It also defines the `qpid-primary` script which does
not actually start a new service, rather it promotes the existing
`qpidd` broker to primary status.

The `resources` section also defines a virtual IP address for clients:
`20.0.20.200`.

`qpidd.conf` should contain these lines:

    ha-cluster=yes
    ha-brokers-url=20.0.20.1,20.0.20.2,20.0.20.3
        

The brokers connect to each other directly via the addresses listed in
`ha-brokers-url`. Note the client and broker addresses are on separate
sub-nets, this is recommended but not required.

The `service` section defines 3 `qpidd` services, one for each node.
Each service is in a restricted fail-over domain containing just that
node, and has the `restart` recovery policy. The effect of this is that
rgmanager will run `qpidd` on each node, restarting if it fails.

There is a single `qpidd-primary-service` using the `qpidd-primary`
script which is not restricted to a domain and has the `relocate`
recovery policy. This means rgmanager will start `qpidd-primary` on one
of the nodes when the cluster starts and will relocate it to another
node if the original node fails. Running the `qpidd-primary` script does
not start a new broker process, it promotes the existing broker to
become the primary.

### <span class="header-section-number">1.5.1</span> Shutting down qpidd on a HA node

As explained above both the per-node `qpidd` service and the
re-locatable `qpidd-primary` service are implemented by the same `qpidd`
daemon.

As a result, stopping the `qpidd` service will not stop a `qpidd` daemon
that is acting as primary, and stopping the `qpidd-primary` service will
not stop a `qpidd` process that is acting as backup.

To shut down a node that is acting as primary you need to shut down the
`qpidd` service *and* relocate the primary:

    clusvcadm -d somenode-qpidd-service
    clusvcadm -r qpidd-primary-service
            

This will shut down the `qpidd` daemon on that node and prevent the
primary service service from relocating back to the node because the
qpidd service is no longer running there.

## <span class="header-section-number">1.6</span> Broker Administration Tools

Normally, clients are not allowed to connect to a backup broker. However
management tools are allowed to connect to a backup brokers. If you use
these tools you *must not* add or remove messages from replicated
queues, nor create or delete replicated queues or exchanges as this will
disrupt the replication process and may cause message loss.

`qpid-ha` allows you to view and change HA configuration settings.

The tools `qpid-config`, `qpid-route` and `qpid-stat` will connect to a
backup if you pass the flag `ha-admin` on the command line.

## <span class="header-section-number">1.7</span> Controlling replication of queues and exchanges

By default, queues and exchanges are not replicated automatically. You
can change the default behaviour by setting the `ha-replicate`
configuration option. It has one of the following values:

-   all: Replicate everything automatically: queues, exchanges, bindings
    and messages.

-   configuration: Replicate the existence of queues, exchange and
    bindings but don't replicate messages.

-   none: Don't replicate anything, this is the default.

You can over-ride the default for a particular queue or exchange by
passing the argument `qpid.replicate` when creating the queue or
exchange. It takes the same values as `ha-replicate`

Bindings are automatically replicated if the queue and exchange being
bound both have replication `all` or `configuration`, they are not
replicated otherwise.

You can create replicated queues and exchanges with the `qpid-config`
management tool like this:

    qpid-config add queue myqueue --replicate all
        

To create replicated queues and exchanges via the client API, add a
`node` entry to the address like this:

    "myqueue;{create:always,node:{x-declare:{arguments:{'qpid.replicate':all}}}}"
        

There are some built-in exchanges created automatically by the broker,
these exchanges are never replicated. The built-in exchanges are the
default (nameless) exchange, the AMQP standard exchanges
(`amq.direct, amq.topic, amq.fanout` and `amq.match`) and the management
exchanges (`qpid.management, qmf.default.direct` and
`qmf.default.topic`)

Note that if you bind a replicated queue to one of these exchanges, the
binding will *not* be replicated, so the queue will not have the binding
after a fail-over.

## <span class="header-section-number">1.8</span> Client Connection and Fail-over

Clients can only connect to the primary broker. Backup brokers reject
any connection attempt by a client. Clients rejected by a backup broker
will automatically fail-over until they connect to the primary.

Clients are configured with the URL for the cluster (details below for
each type of client). There are two possibilities

-   The URL contains multiple addresses, one for each broker in the
    cluster.

-   The URL contains a single virtual IP address that is assigned to the
    primary broker by the resource manager. This is the recommended
    configuration.

In the first case, clients will repeatedly re-try each address in the
URL until they successfully connect to the primary. In the second case
the resource manager will assign the virtual IP address to the primary
broker, so clients only need to re-try on a single address.

When the primary broker fails, clients re-try all known cluster
addresses until they connect to the new primary. The client re-sends any
messages that were previously sent but not acknowledged by the broker at
the time of the failure. Similarly messages that have been sent by the
broker, but not acknowledged by the client, are re-queued.

TCP can be slow to detect connection failures. A client can configure a
connection to use a heartbeat to detect connection failure, and can
specify a time interval for the heartbeat. If heartbeats are in use,
failures will be detected no later than twice the heartbeat interval.
The following sections explain how to enable heartbeat in each client.

Note: the following sections explain how to configure clients with
multiple dresses, but if you are using a virtual IP address you only
need to configure that one address for clients, you don't need to list
all the addresses.

Suppose your cluster has 3 nodes: `node1`, `node2` and `node3` all using
the default AMQP port, and you are not using a virtual IP address. To
connect a client you need to specify the address(es) and set the
`reconnect` property to `true`. The following sub-sections show how to
connect each type of client.

### <span class="header-section-number">1.8.1</span> C++ clients

With the C++ client, you specify multiple cluster addresses in a single
URL <span id="fnref5">[^5^](#fn5)</span> You also need to specify the
connection option `reconnect` to be true. For example:

    qpid::messaging::Connection c("node1,node2,node3","{reconnect:true}");
          

Heartbeats are disabled by default. You can enable them by specifying a
heartbeat interval (in seconds) for the connection via the `heartbeat`
option. For example:

    qpid::messaging::Connection c("node1,node2,node3","{reconnect:true,heartbeat:10}");
          

### <span class="header-section-number">1.8.2</span> Python clients

With the python client, you specify `reconnect=True` and a list of
host:port addresses as `reconnect_urls` when calling
`Connection.establish` or `Connection.open`

    connection = qpid.messaging.Connection.establish("node1", reconnect=True, reconnect_urls=["node1", "node2", "node3"])
          

Heartbeats are disabled by default. You can enable them by specifying a
heartbeat interval (in seconds) for the connection via the 'heartbeat'
option. For example:

    connection = qpid.messaging.Connection.establish("node1", reconnect=True, reconnect_urls=["node1", "node2", "node3"], heartbeat=10)
          

### <span class="header-section-number">1.8.3</span> Java JMS Clients

In Java JMS clients, client fail-over is handled automatically if it is
enabled in the connection. You can configure a connection to use
fail-over using the `failover` property:

        connectionfactory.qpidConnectionfactory = amqp://guest:guest@clientid/test?brokerlist='tcp://localhost:5672'&failover='failover_exchange'
          

This property can take three values:

failover\_exchange  
If the connection fails, fail over to any other broker in the cluster.

roundrobin  
If the connection fails, fail over to one of the brokers specified in
the `brokerlist`.

singlebroker  
Fail-over is not supported; the connection is to a single broker only.

In a Connection URL, heartbeat is set using the `heartbeat` property,
which is an integer corresponding to the heartbeat period in seconds.
For instance, the following line from a JNDI properties file sets the
heartbeat time out to 3 seconds:

        connectionfactory.qpidConnectionfactory = amqp://guest:guest@clientid/test?brokerlist='tcp://localhost:5672'&heartbeat='3'
          

## <span class="header-section-number">1.9</span> Security and Access Control.

This section outlines the HA specific aspects of security configuration.
Please see ? for more details on enabling authentication and setting up
Access Control Lists.

> **Note**
>
> Unless you disable authentication with `auth=no` in your
> configuration, you *must* set the options below and you *must* have an
> ACL file with at least the entry described below.
>
> Backups will be *unable to connect to the primary* if the security
> configuration is incorrect. See also ?

When authentication is enabled you must set the credentials used by HA
brokers with following options:

HA Security Options

HA Security Options

`ha-username` USER

User name for HA brokers. Note this must *not* include the `@QPID`
suffix.

`ha-password` PASS

Password for HA brokers.

`ha-mechanism` MECHANISM

Mechanism for HA brokers. Any mechanism you enable for broker-to-broker
communication can also be used by a client, so do not use
ha-mechanism=ANONYMOUS in a secure environment.

This identity is used to authorize federation links from backup to
primary. It is also used to authorize actions on the backup to replicate
primary state, for example creating queues and exchanges.

When authorization is enabled you must have an Access Control List with
the following rule to allow HA replication to function. Suppose
`ha-username`=USER

    acl allow USER@QPID all all
        

## <span class="header-section-number">1.10</span> Integrating with other Cluster Resource Managers

To integrate with a different resource manager you must configure it to:

-   Start a qpidd process on each node of the cluster.

-   Restart qpidd if it crashes.

-   Promote exactly one of the brokers to primary.

-   Detect a failure and promote a new primary.

The `qpid-ha` command allows you to check if a broker is primary, and to
promote a backup to primary.

To test if a broker is the primary:

    qpid-ha -b broker-address status --expect=primary

This will return 0 if the broker at broker-address is the primary, non-0
otherwise.

To promote a broker to primary:

    qpid-ha --cluster-manager -b broker-address promote

Note that `promote` is considered a "cluster manager only" command.
Incorrect use of `promote` outside of the cluster manager could create a
cluster with multiple primaries. Such a cluster will malfunction and
lose data. "Cluster manager only" commands are not accessible in
`qpid-ha` without the `--cluster-manager` option.

To list the full set of commands use:

    qpid-ha --cluster-manager --help
        

## <span class="header-section-number">1.11</span> Using a message store in a cluster

If you use a persistent store for your messages then each broker in a
cluster will have its own store. If the entire cluster fails and is
restarted, the \*first\* broker that becomes primary will recover from
its store. All the other brokers will clear their stores and get an
update from the primary to ensure consistency.

## <span class="header-section-number">1.12</span> Troubleshooting a cluster

This section applies to clusters that are using rgmanager as the cluster
manager.

### <span class="header-section-number">1.12.1</span> No primary broker

When you initially start a HA cluster, all brokers are in `joining`
mode. The brokers do not automatically select a primary, they rely on
the cluster manager `rgmanager` to do so. If `rgmanager` is not running
or is not configured correctly, brokers will remain in the `joining`
state. See ?

### <span class="header-section-number">1.12.2</span> Authentication and ACL failures

If a broker is unable to establish a connection to another broker in the
cluster due to authentication or ACL problems the logs may contain
errors like the following:

    info SASL: Authentication failed: SASL(-13): user not found: Password verification failed
        

    warning Client closed connection with 320: User anonymous@QPID federation connection denied. Systems with authentication enabled must specify ACL create link rules.
        

    warning Client closed connection with 320: ACL denied anonymous@QPID creating a federation link.
        

Set the HA security configuration and ACL file as described in ?. Once
the cluster is running and the primary is promoted , run:

    qpid-ha status --all

to make sure that the brokers are running as one cluster.

### <span class="header-section-number">1.12.3</span> Slow recovery times

The following configuration settings affect recovery time. The values
shown are examples that give fast recovery on a lightly loaded system.
You should run tests to determine if the values are appropriate for your
system and load conditions.

#### <span class="header-section-number">1.12.3.1</span> cluster.conf:

    <rm status_poll_interval=1>
        

status\_poll\_interval is the interval in seconds that the resource
manager checks the status of managed services. This affects how quickly
the manager will detect failed services.

    <ip address="20.0.20.200" monitor_link="yes" sleeptime="0"/>
        

This is a virtual IP address for client traffic. monitor\_link="yes"
means monitor the health of the network interface used for the VIP.
sleeptime="0" means don't delay when failing over the VIP to a new
address.

#### <span class="header-section-number">1.12.3.2</span> qpidd.conf

    link-maintenance-interval=0.1
        

Interval for backup brokers to check the link to the primary re-connect
if need be. Default 2 seconds. Can be set lower for faster fail-over.
Setting too low will result in excessive link-checking activity on the
broker.

    link-heartbeat-interval=5
        

Heartbeat interval for federation links. The HA cluster uses federation
links between the primary and each backup. The primary can take up to
twice the heartbeat interval to detect a failed backup. When a sender
sends a message the primary waits for all backups to acknowledge before
acknowledging to the sender. A disconnected backup may cause the primary
to block senders until it is detected via heartbeat.

This interval is also used as the timeout for broker status checks by
rgmanager. It may take up to this interval for rgmanager to detect a
hung broker.

The default of 120 seconds is very high, you will probably want to set
this to a lower value. If set too low, under network congestion or heavy
load, a slow-to-respond broker may be re-started by rgmanager.

### <span class="header-section-number">1.12.4</span> Total cluster failure

Note: for definition of broker states joining, catch-up, ready,
recovering and active see ?

The cluster can only guarantee availability as long as there is at least
one active primary broker or ready backup broker left alive. If all the
brokers fail simultaneously, the cluster will fail and non-persistent
data will be lost.

While there is an active primary broker, clients can get service. If the
active primary fails, one of the "ready" backup brokers will take over,
recover and become active. Note a backup can only be promoted to primary
if it is in the "ready" state (with the exception of the first primary
in a new cluster where all brokers are in the "joining" state)

Given a stable cluster of N brokers with one active primary and N-1
ready backups, the system can sustain up to N-1 failures in rapid
succession. The surviving broker will be promoted to active and continue
to give service.

However at this point the system *cannot* sustain a failure of the
surviving broker until at least one of the other brokers recovers,
catches up and becomes a ready backup. If the surviving broker fails
before that the cluster will fail in one of two modes (depending on the
exact timing of failures)

#### <span class="header-section-number">1.12.4.1</span> 1. The cluster hangs

All brokers are in joining or catch-up mode. rgmanager tries to promote
a new primary but cannot find any candidates and so gives up. clustat
will show that the qpidd services are running but the the qpidd-primary
service has stopped, something like this:

    Service Name                   Owner (Last)                   State
    ------- ----                   ----- ------                   -----
    service:mrg33-qpidd-service    20.0.10.33                     started
    service:mrg34-qpidd-service    20.0.10.34                     started
    service:mrg35-qpidd-service    20.0.10.35                     started
    service:qpidd-primary-service  (20.0.10.33)                   stopped
        

Eventually all brokers become stuck in "joining" mode, as shown by:
`qpid-ha status --all`

At this point you need to restart the cluster in one of the following
ways:

1.  Restart the entire cluster: In `luci:your-cluster:Nodes` click
    reboot to restart the entire cluster

2.  Stop and restart the cluster with `ccs --stopall; ccs --startall`

3.  Restart just the Qpid services:In `luci:your-cluster:Service Groups`

    1.  Select all the qpidd (not qpidd-primary) services, click restart

    2.  Select the qpidd-primary service, click restart

4.  Stop the `qpidd-primary` and `qpidd` services with `clusvcadm`, then
    restart (qpidd-primary last)

#### <span class="header-section-number">1.12.4.2</span> 2. The cluster reboots

A new primary is promoted and the cluster is functional but all
non-persistent data from before the failure is lost.

### <span class="header-section-number">1.12.5</span> Fencing and network partitions

A network partition is a a network failure that divides the cluster into
two or more sub-clusters, where each broker can communicate with brokers
in its own sub-cluster but not with brokers in other sub-clusters. This
condition is also referred to as a "split brain".

Nodes in one sub-cluster can't tell whether nodes in other sub-clusters
are dead or are still running but disconnected. We cannot allow each
sub-cluster to independently declare its own qpidd primary and start
serving clients, as the cluster will become inconsistent. We must ensure
only one sub-cluster continues to provide service.

A *quorum* determines which sub-cluster continues to operate, and *power
fencing* ensures that nodes in non-quorate sub-clusters cannot attempt
to provide service inconsistently. For more information see:

https://access.redhat.com/site/documentation/en-US/Red\_Hat\_Enterprise\_Linux/6/html-single/High\_Availability\_Add-On\_Overview/index.html,
chapter 2. Quorum and 4. Fencing.

------------------------------------------------------------------------

1.  <div id="fn1">

    </div>

    You can control the maximum number of messages in the buffer by
    setting the client's `capacity`. For details of how to set the
    capacity in client code see "Using the Qpid Messaging API" in
    Programming in Apache Qpid.[↩](#fnref1)

2.  <div id="fn2">

    </div>

    Clients must use "at-least-once" reliability to enable re-send of
    unacknowledged messages. This is the default behaviour, no options
    need be set to enable it. For details of client addressing options
    see "Using the Qpid Messaging API" in Programming in Apache
    Qpid.[↩](#fnref2)

3.  <div id="fn3">

    </div>

    The full format of the URL is given by this grammar:

        url = ["amqp:"][ user ["/" password] "@" ] addr ("," addr)*
        addr = tcp_addr / rmda_addr / ssl_addr / ...
        tcp_addr = ["tcp:"] host [":" port]
        rdma_addr = "rdma:" host [":" port]
        ssl_addr = "ssl:" host [":" port]'
                  

    [↩](#fnref3)

4.  <div id="fn4">

    </div>

    Values specified as SECONDS can be a fraction of a second, e.g.
    "0.1" for a tenth of a second. They can also have an explicit unit,
    e.g. 10s (seconds), 10ms (milliseconds), 10us (microseconds), 10ns
    (nanoseconds)[↩](#fnref4)

5.  <div id="fn5">

    </div>

    The full grammar for the URL is:

        url = ["amqp:"][ user ["/" password] "@" ] addr ("," addr)*
        addr = tcp_addr / rmda_addr / ssl_addr / ...
        tcp_addr = ["tcp:"] host [":" port]
        rdma_addr = "rdma:" host [":" port]
        ssl_addr = "ssl:" host [":" port]'
              

    [↩](#fnref5)


