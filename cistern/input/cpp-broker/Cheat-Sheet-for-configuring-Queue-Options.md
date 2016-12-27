# <span class="header-section-number">1</span> Cheat Sheet for configuring Queue Options

## <span class="header-section-number">1.1</span> Configuring Queue Options

The C++ Broker M4 or later supports the following additional Queue
constraints.

-   ?

-   -   ?

    -   ?

    -   ?

    -   -   ?

    -   ?

The 0.10 C++ Broker supports the following additional Queue
configuration options:

-   ?

### <span class="header-section-number">1.1.1</span> Applying Queue Sizing Constraints

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

### <span class="header-section-number">1.1.2</span> Changing the Queue ordering Behaviors (FIFO/LVQ)

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

### <span class="header-section-number">1.1.3</span> Setting additional behaviors

### <span class="header-section-number">1.1.4</span> Other Clients

Note that these options can be set from any client. QueueOptions just
correctly formats the arguments passed to the QueueDeclare() method.
