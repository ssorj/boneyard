# Queues

[Up to Wiring](wiring.html)

XXX Ugh

## Configuring Queue Options

The C++ Broker M4 or later supports the following additional Queue
constraints.

-   ?

-   -   ?

    -   ?

    -   ?

    -   -   ?

        -   ?

    -   ?

The 0.10 C++ Broker supports the following additional Queue
configuration options:

-   ?

### Applying Queue Sizing Constraints

This allows to specify how to size a queue and what to do when the
sizing constraints have been reached. The queue size can be limited by
the number messages (message depth) or byte depth on the queue.

Once the Queue meets/ exceeds these constraints the follow policies can
be applied

-   REJECT - Reject the published message

-   FLOW\_TO\_DISK - Flow the messages to disk, to preserve memory

-   RING - start overwriting messages in a ring based on sizing. If head
    meets tail, advance head

-   RING\_STRICT - start overwriting messages in a ring based on sizing.
    If head meets tail, AND the consumer has the tail message acquired
    it will reject

Examples:

Create a queue an auto delete queue that will support 100 000 bytes, and
then REJECT

    #include "qpid/client/QueueOptions.h"

        QueueOptions qo;
        qo.setSizePolicy(REJECT,100000,0);

        session.queueDeclare(arg::queue=queue, arg::autoDelete=true, arg::arguments=qo);

Create a queue that will support 1000 messages into a RING buffer

    #include "qpid/client/QueueOptions.h"

        QueueOptions qo;
        qo.setSizePolicy(RING,0,1000);

        session.queueDeclare(arg::queue=queue, arg::arguments=qo);

### Changing the Queue ordering Behaviors (FIFO/LVQ)

The default ordering in a queue in Qpid is FIFO. However additional
ordering semantics can be used namely LVQ (Last Value Queue). Last Value
Queue is define as follows.

If I publish symbols RHT, IBM, JAVA, MSFT, and then publish RHT before
the consumer is able to consume RHT, that message will be over written
in the queue and the consumer will receive the last published value for
RHT.

Example:

    #include "qpid/client/QueueOptions.h"

        QueueOptions qo;
        qo.setOrdering(LVQ);

        session.queueDeclare(arg::queue=queue, arg::arguments=qo);

        .....
        string key;
        qo.getLVQKey(key);

        ....
        for each message, set the into application headers before transfer
        message.getHeaders().setString(key,"RHT");
        

Notes:

-   Messages that are dequeued and the re-queued will have the following
    exceptions. a.) if a new message has been queued with the same key,
    the re-queue from the consumer, will combine these two messages. b.)
    If an update happens for a message of the same key, after the
    re-queue, it will not update the re-queued message. This is done to
    protect a client from being able to adversely manipulate the queue.

-   Acquire: When a message is acquired from the queue, no matter it's
    position, it will behave the same as a dequeue

-   LVQ does not support durable messages. If the queue or messages are
    declared durable on an LVQ, the durability will be ignored.

A fully worked ? can be found here

### Setting additional behaviors

#### Persist Last Node

This option is used in conjunction with clustering. It allows for a
queue configured with this option to persist transient messages if the
cluster fails down to the last node. If additional nodes in the cluster
are restored it will stop persisting transient messages.

Note

-   if a cluster is started with only one active node, this mode will
    not be triggered. It is only triggered the first time the cluster
    fails down to 1 node.

-   The queue MUST be configured durable

Example:

    #include "qpid/client/QueueOptions.h"

        QueueOptions qo;
        qo.clearPersistLastNode();

        session.queueDeclare(arg::queue=queue, arg::durable=true, arg::arguments=qo);

#### Queue event generation

This option is used to determine whether enqueue/dequeue events
representing changes made to queue state are generated. These events can
then be processed by plugins such as that used for ?.

Example:

    #include "qpid/client/QueueOptions.h"

        QueueOptions options;
        options.enableQueueEvents(1);
        session.queueDeclare(arg::queue="my-queue", arg::arguments=options);

The boolean option indicates whether only enqueue events should be
generated. The key set by this is 'qpid.queue\_event\_generation' and
the value is and integer value of 1 (to replicate only enqueue events)
or 2 (to replicate both enqueue and dequeue events).

### Other Clients

Note that these options can be set from any client. QueueOptions just
correctly formats the arguments passed to the QueueDeclare() method.
