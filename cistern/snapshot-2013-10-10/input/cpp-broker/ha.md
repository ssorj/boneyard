# High Availability

[Up to Index](index.html)

## Overview

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
[Rgmanager](https://fedorahosted.org/cluster/wiki/RGManager) is
supported initially, but others may be supported in the future.

### Avoiding message loss

In order to avoid message loss, the primary broker *delays
acknowledgment* of messages received from clients until the message has
been replicated and acknowledged by all of the back-up brokers, or has
been consumed from the primary queue.

This ensures that all acknowledged messages are safe: they have either
been consumed or backed up to all backup brokers. Messages that are
consumed *before* they are replicated do not need to be replicated. This
reduces the work load when replicating a queue with active consumers.

Clients keep *unacknowledged* messages in a buffer [^1] until they are
acknowledged by the primary. If the primary fails, clients will
fail-over to the new primary and *re-send* all their unacknowledged
messages. [^2]

If the primary crashes, all the *acknowledged* messages will be
available on the backup that takes over as the new primary. The
*unacknowledged* messages will be re-sent by the clients. Thus no
messages are lost.

Note that this means it is possible for messages to be *duplicated*. In
the event of a failure it is possible for a message to received by the
backup that becomes the new primary *and* re-sent by the client. The
application must take steps to identify and eliminate duplicates.

When a new primary is promoted after a fail-over it is initially in
"recovering" mode. In this mode, it delays acknowledgment of messages on
behalf of all the backups that were connected to the previous primary.
This protects those messages against a failure of the new primary until
the backups have a chance to connect and catch up.

Not all messages need to be replicated to the back-up brokers. If a
message is consumed and acknowledged by a regular client before it has
been replicated to a backup, then it doesn't need to be replicated.

Joining
:   Initial status of a new broker that has not yet connected to the
    primary.

Catch-up
:   A backup broker that is connected to the primary and catching up on
    queues and messages.

Ready
:   A backup broker that is fully caught-up and ready to take over as
    primary.

Recovering
:   The newly-promoted primary, waiting for backups to connect and catch
    up.

Active
:   The active primary broker with all backups connected and caught-up.

### Limitations

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

## Virtual IP Addresses

Some resource managers (including `rgmanager`) support virtual IP
addresses. A virtual IP address is an IP address that can be relocated
to any of the nodes in a cluster. The resource manager associates this
address with the primary node in the cluster, and relocates it to the
new primary when there is a failure. This simplifies configuration as
you can publish a single IP address rather than a list.

A virtual IP address can be used by clients to connect to the primary.
The following sections will explain how to configure virtual IP
addresses for clients or brokers.

## Configuring the Brokers

The broker must load the `ha` module, it is loaded by default. The
following broker options are available for the HA module.

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Options for High Availability Messaging Cluster
  ------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  `ha-cluster `                                     Set to "yes" to have the broker join a cluster.

  `ha-queue-replication `                           Enable replication of specific queues without joining a cluster, see ?.

  `ha-brokers-url `                                 The URL [^3] used by cluster brokers to connect to each other. The URL should contain a comma separated list of the broker addresses, rather than a virtual IP address.

  `ha-public-url `                                  The URL is advertised to clients as the "known-hosts" for fail-over. It can be a list or a single virtual IP address. A virtual IP address is recommended.
                                                    
                                                    Using this option you can put client and broker traffic on separate networks, which is recommended.
                                                    
                                                    Note: When HA clustering is enabled the broker option `known-hosts-url` is ignored and over-ridden by the `ha-public-url` setting.

  `ha-replicate `VALUE                              Specifies whether queues and exchanges are replicated by default. VALUE is one of: `none`, `configuration`, `all`. For details see ?.

  `ha-username `                                    Authentication settings used by HA brokers to connect to each other. If you are using authorization (?) then this user must have all permissions.
                                                    
  `ha-password `                                    
                                                    
  `ha-mechanism `                                   

  `ha-backup-timeout` [^4]                          Maximum time that a recovering primary will wait for an expected backup to connect and become ready.

  `link-maintenance-interval `                      Interval for the broker to check link health and re-connect links if need be. If you want brokers to fail over quickly you can set this to a fraction of a second, for example: 0.1.

  `link-heartbeat-interval `                        Heartbeat interval for replication links. The link will be assumed broken if there is no heartbeat for twice the interval.
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  : Broker Options for High Availability Messaging Cluster

To configure a HA cluster you must set at least `ha-cluster` and
`ha-brokers-url`.

## The Cluster Resource Manager

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

## Configuring `rgmanager` as resource manager

This section assumes that you are already familiar with setting up and
configuring clustered services using `cman` and `rgmanager`. It will
show you how to configure an active-passive, hot-standby `qpidd` HA
cluster with `rgmanager`.

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
      <!-- The cluster has 3 nodes. Each has a unique nodid and one vote
           for quorum. -->
      <clusternodes>
        <clusternode name="node1.example.com" nodeid="1"/>
        <clusternode name="node2.example.com" nodeid="2"/>
        <clusternode name="node3.example.com" nodeid="3"/>
      </clusternodes>
      <!-- Resouce Manager configuration. -->
      <rm>
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

          <!-- This is a virtual IP address for client traffic. -->
          <ip address="20.0.20.200" monitor_link="1"/>
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

The `resources` section also defines a pair of virtual IP addresses on
different sub-nets. One will be used for broker-to-broker communication,
the other for client-to-broker.

To take advantage of the virtual IP addresses, `qpidd.conf` should
contain these lines:

          ha-cluster=yes
          ha-public-url=20.0.10.200
          ha-brokers-url=20.0.20.1,20.0.20.2,20.0.20.3
        

This configuration allows clients to connect to a single address:
20.0.10.200. The brokers connect to each other directly via the
addresses listed in `ha-brokers-url`. Note the client and broker
addresses are on separate sub-nets, this is recommended but not
required.

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

## Broker Administration Tools

Normally, clients are not allowed to connect to a backup broker. However
management tools are allowed to connect to a backup brokers. If you use
these tools you *must not* add or remove messages from replicated
queues, nor create or delete replicated queues or exchanges as this will
disrupt the replication process and may cause message loss.

`qpid-ha` allows you to view and change HA configuration settings.

The tools `qpid-config`, `qpid-route` and `qpid-stat` will connect to a
backup if you pass the flag `ha-admin` on the command line.

## Controlling replication of queues and exchanges

By default, queues and exchanges are not replicated automatically. You
can change the default behavior by setting the `ha-replicate`
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

## Client Connection and Fail-over

Clients can only connect to the primary broker. Backup brokers reject
any connection attempt by a client. Clients rejected by a backup broker
will automatically fail-over until they connect to the primary. if
`ha-public-url` contains multiple addresses, the client will them all in
rotation. If it is a virtual IP address the clients will retry on the
same address until it is reconnected.

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

### C++ clients

With the C++ client, you specify multiple cluster addresses in a single
URL [^5] You also need to specify the connection option `reconnect` to
be true. For example:

        qpid::messaging::Connection c("node1,node2,node3","{reconnect:true}");
          

Heartbeats are disabled by default. You can enable them by specifying a
heartbeat interval (in seconds) for the connection via the `heartbeat`
option. For example:

          qpid::messaging::Connection c("node1,node2,node3","{reconnect:true,heartbeat:10}");
        

### Python clients

With the python client, you specify `reconnect=True` and a list of
host:port addresses as `reconnect_urls` when calling
`Connection.establish` or `Connection.open`

        connection = qpid.messaging.Connection.establish("node1", reconnect=True, reconnect_urls=["node1", "node2", "node3"])
          

Heartbeats are disabled by default. You can enable them by specifying a
heartbeat interval (in seconds) for the connection via the 'heartbeat'
option. For example:

        connection = qpid.messaging.Connection.establish("node1", reconnect=True, reconnect_urls=["node1", "node2", "node3"], heartbeat=10)
          

### Java JMS Clients

In Java JMS clients, client fail-over is handled automatically if it is
enabled in the connection. You can configure a connection to use
fail-over using the `failover` property:

        connectionfactory.qpidConnectionfactory = amqp://guest:guest@clientid/test?brokerlist='tcp://localhost:5672'&failover='failover_exchange'
          

This property can take three values:

failover\_exchange
:   If the connection fails, fail over to any other broker in the
    cluster.

roundrobin
:   If the connection fails, fail over to one of the brokers specified
    in the `brokerlist`.

singlebroker
:   Fail-over is not supported; the connection is to a single broker
    only.

In a Connection URL, heartbeat is set using the `idle_timeout` property,
which is an integer corresponding to the heartbeat period in seconds.
For instance, the following line from a JNDI properties file sets the
heartbeat time out to 3 seconds:

        connectionfactory.qpidConnectionfactory = amqp://guest:guest@clientid/test?brokerlist='tcp://localhost:5672',idle_timeout=3
          

## Security.

You can secure your cluster using the authentication and authorization
features described in ?.

Backup brokers connect to the primary broker and subscribe for
management events and queue contents. You can specify the identity used
to connect to the primary with the following options:

  -------------------------------------------------------------------------
  Security options
  for High
  Availability
  Messaging Cluster
  ------------------ ------------------------------------------------------
  `ha-username `     Authentication settings used by HA brokers to connect
                     to each other. If you are using authorization (?) then
  `ha-password `     this user must have all permissions.
                     
  `ha-mechanism `    
  -------------------------------------------------------------------------

  : Security options for High Availability Messaging Cluster

This identity is also used to authorize actions taken on the backup
broker to replicate from the primary, for example to create queues or
exchanges.

## Integrating with other Cluster Resource Managers

To integrate with a different resource manager you must configure it to:

-   Start a qpidd process on each node of the cluster.

-   Restart qpidd if it crashes.

-   Promote exactly one of the brokers to primary.

-   Detect a failure and promote a new primary.

The `qpid-ha` command allows you to check if a broker is primary, and to
promote a backup to primary.

To test if a broker is the primary:

        qpid-ha -b  status --expect=primary
          

This command will return 0 if the broker at broker-address is the
primary, non-0 otherwise.

To promote a broker to primary:

        qpid-ha -b  promote
          

`qpid-ha --help` gives information on other commands and options
available. You can also use `qpid-ha` to manually examine and promote
brokers. This can be useful for testing failover scenarios without
having to set up a full resource manager, or to simulate a cluster on a
single node. For deployment, a resource manager is required.

## Using a message store in a cluster

If you use a persistent store for your messages then each broker in a
cluster will have its own store. If the entire cluster fails and is
restarted, the \*first\* broker that becomes primary will recover from
its store. All the other brokers will clear their stores and get an
update from the primary to ensure consistency.

[^1]: You can control the maximum number of messages in the buffer by
    setting the client's `capacity`. For details of how to set the
    capacity in client code see "Using the Qpid Messaging API" in
    Programming in Apache Qpid.

[^2]: Clients must use "at-least-once" reliability to enable re-send of
    unacknowledged messages. This is the default behavior, no options
    need be set to enable it. For details of client addressing options
    see "Using the Qpid Messaging API" in Programming in Apache Qpid.

[^3]: The full format of the URL is given by this grammar:

        url = ["amqp:"][ user ["/" password] "@" ] addr ("," addr)*
        addr = tcp_addr / rmda_addr / ssl_addr / ...
        tcp_addr = ["tcp:"] host [":" port]
        rdma_addr = "rdma:" host [":" port]
        ssl_addr = "ssl:" host [":" port]'
                  

[^4]: Values specified as SECONDS can be a fraction of a second, e.g.
    "0.1" for a tenth of a second. They can also have an explicit unit,
    e.g. 10s, 10ms, 10us, 10ns

[^5]: The full grammar for the URL is:

                url = ["amqp:"][ user ["/" password] "@" ] addr ("," addr)*
                addr = tcp_addr / rmda_addr / ssl_addr / ...
                tcp_addr = ["tcp:"] host [":" port]
                rdma_addr = "rdma:" host [":" port]
                ssl_addr = "ssl:" host [":" port]'
              
