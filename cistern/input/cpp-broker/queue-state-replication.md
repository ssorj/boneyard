# <span class="header-section-number">1</span> Queue State Replication

## <span class="header-section-number">1.1</span> Asynchronous Replication of Queue State

### <span class="header-section-number">1.1.1</span> Overview

There is support in qpidd for selective asynchronous replication of
queue state. This is achieved by:

\(a) enabling event generation for the queues in question

\(b) loading a plugin on the 'source' broker to encode those events as
messages on a replication queue (this plugin is called
replicating\_listener.so)

\(c) loading a custom exchange plugin on the 'backup' broker (this plugin
is called replication\_exchange.so)

\(d) creating an instance of the replication exchange type on the backup
broker

\(e) establishing a federation bridge between the replication queue on
the source broker and the replication exchange on the backup broker

The bridge established between the source and backup brokers for
replication (step (e) above) should have acknowledgements turned on
(this may be done through the --ack N option to qpid-route). This
ensures that replication events are not lost if the bridge fails.

The replication protocol will also eliminate duplicates to ensure
reliably replicated state. Note though that only one bridge per
replication exchange is supported. If clients try to publish to the
replication exchange or if more than a the single required bridge from
the replication queue on the source broker is created, replication will
be corrupted. (Access control may be used to restrict access and help
prevent this).

The replicating event listener plugin (step (b) above) has the following
options:

    Queue Replication Options:
      --replication-queue QUEUE                      Queue on which events for
                                                     other queues are recorded
      --replication-listener-name NAME (replicator)  name by which to register the
                                                     replicating event listener
      --create-replication-queue                     if set, the replication will
                                                     be created if it does not
                                                     exist
          

The name of the queue is required. It can either point to a durable
queue whose definition has been previously recorded, or
the --create-replication-queue option can be specified in which case the
queue will be created a simple non-durable queue if it does not already
exist.

### <span class="header-section-number">1.1.2</span> Use with Clustering

The source and/or backup brokers may also be clustered brokers. In this
case the federated bridge will be re-established between replicas should
either of the originally connected nodes fail. There are however the
following limitations at present:

-   The backup site does not process membership updates after it
    establishes the first connection. In order for newly added members
    on a source cluster to be eligible as failover targets, the bridge
    must be recreated after those members have been added to the source
    cluster.

<!-- -->

-   New members added to a backup cluster will not receive information
    about currently established bridges. Therefore in order to allow the
    bridge to be re-established from these members in the event of
    failure of older nodes, the bridge must be recreated after the new
    members have joined.

<!-- -->

-   Only a single URL can be passed to create the initial link from
    backup site to the primary site. this means that at the time of
    creating the initial connection the initial node in the primary site
    to which the connection is made needs to be running. Once connected
    the backup site will receive a membership update of all the nodes in
    the primary site, and if the initial connection node in the primary
    fails, the link will be re-established on the next node that was
    started (time) on the primary site.

Due to the acknowledged transfer of events over the bridge (see note
above) manual recreation of the bridge and automatic re-establishment of
te bridge after connection failure (including failover where either or
both ends are clustered brokers) will not result in event loss.

### <span class="header-section-number">1.1.3</span> Operations on Backup Queues

When replicating the state of a queue to a backup broker it is important
to recognise that any other operations performed directly on the backup
queue may break the replication.

If the backup queue is to be an active (i.e. accessed by clients while
replication is on) only enqueues should be selected for replication. In
this mode, any message enqueued on the source brokers copy of the queue
will also be enqueued on the backup brokers copy. However not attempt
will be made to remove messages from the backup queue in response to
removal of messages from the source queue.

### <span class="header-section-number">1.1.4</span> Selecting Queues for Replication

Queues are selected for replication by specifying the types of events
they should generate (it is from these events that the replicating
plugin constructs messages which are then pulled and processed by the
backup site). This is done through options passed to the initial
queue-declare command that creates the queue and may be done either
through qpid-config or similar tools, or by the application.

With qpid-config, the --generate-queue-events options is used:

        --generate-queue-events N
                             If set to 1, every enqueue will generate an event that can be processed by
                             registered listeners (e.g. for replication). If set to 2, events will be
                             generated for enqueues and dequeues
          

From an application, the arguments field of the queue-declare AMQP
command is used to convey this information. An entry should be added to
the map with key 'qpid.queue\_event\_generation' and an integer value of
1 (to replicate only enqueue events) or 2 (to replicate both enqueue and
dequeue events).

Applications written using the c++ client API may fine the
qpid::client::QueueOptions class convenient. This has a
enableQueueEvents() method on it that can be used to set the option (the
instance of QueueOptions is then passed as the value of the arguments
field in the queue-declare command. The boolean option to that method
should be set to true if only enequeue events should be replicated; by
default it is false meaning that both enqueues and dequeues will be
replicated. E.g.

        QueueOptions options;
        options.enableQueueEvents(false);
        session.queueDeclare(arg::queue="my-queue", arg::arguments=options);
          

### <span class="header-section-number">1.1.5</span> Example

Lets assume we will run the primary broker on host1 and the backup on
host2, have installed qpidd on both and have the replicating\_listener
and replication\_exchange plugins in qpidd's module directory(\*1).

On host1 we start the source broker and specifcy that a queue called
'replication' should be used for storing the events until consumed by
the backup. We also request that this queue be created (as transient) if
not already specified:

        qpidd --replication-queue replication-queue --create-replication-queue true --log-enable info+
          

On host2 we start up the backup broker ensuring that the replication
exchange module is loaded:

        qpidd
          

We can then create the instance of that replication exchange that we
will use to process the events:

        qpid-config -a host2 add exchange replication replication-exchange
          

If this fails with the message "Exchange type not implemented:
replication", it means the replication exchange module was not loaded.
Check that the module is installed on your system and if necessary
provide the full path to the library.

We then connect the replication queue on the source broker with the
replication exchange on the backup broker using the qpid-route command:

        qpid-route --ack 50 queue add host2 host1 replication-exchange replication-queue

The example above configures the bridge to acknowledge messages in
batches of 50.

Now create two queues (on both source and backup brokers), one
replicating both enqueues and dequeues (queue-a) and the other
replicating only dequeues (queue-b):

        qpid-config -a host1 add queue queue-a --generate-queue-events 2
        qpid-config -a host1 add queue queue-b --generate-queue-events 1

        qpid-config -a host2 add queue queue-a
        qpid-config -a host2 add queue queue-b
            

We are now ready to use the queues and see the replication.

Any message enqueued on queue-a will be replicated to the backup broker.
When the message is acknowledged by a client connected to host1 (and
thus dequeued), that message will be removed from the copy of the queue
on host2. The state of queue-a on host2 will thus mirror that of the
equivalent queue on host1, albeit with a small lag. (Note however that
we must not have clients connected to host2 publish to-or consume from-
queue-a or the state will fail to replicate correctly due to conflicts).

Any message enqueued on queue-b on host1 will also be enqueued on the
equivalent queue on host2. However the acknowledgement and consequent
dequeuing of messages from queue-b on host1 will have no effect on the
state of queue-b on host2.

(\*1) If not the paths in the above may need to be modified. E.g. if
using modules built from a qpid svn checkout, the following would be
added to the command line used to start qpidd on host1:

        --load-module <path-to-qpid-dir>/src/.libs/replicating_listener.so
            

and the following for the equivalent command line on host2:

        --load-module <path-to-qpid-dir>/src/.libs/replication_exchange.so
            
