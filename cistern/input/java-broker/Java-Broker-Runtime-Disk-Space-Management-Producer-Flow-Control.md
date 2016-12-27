# <span class="header-section-number">1</span> Producer Flow Control

## <span class="header-section-number">1.1</span> General Information

The Java Broker supports a flow control mechanism to which can be used
to prevent either a single queue or an entire virtualhost exceeding
configured limits. These two mechanisms are described next.

## <span class="header-section-number">1.2</span> Server Configuration

### <span class="header-section-number">1.2.1</span> Configuring a Queue to use flow control

Flow control is enabled on a producer when it sends a message to a Queue
which is "overfull". The producer flow control will be rescinded when
all Queues on which a producer is blocking become "underfull". A Queue
is defined as overfull when the size (in bytes) of the messages on the
queue exceeds the *capacity* of the Queue. A Queue becomes "underfull"
when its size becomes less than the *resume capacity*.

The capacity and resume capacity can be specified when the queue is
created. This can be done using the Flow Control Settings within the
Queue creation dialogue.

#### <span class="header-section-number">1.2.1.1</span> Broker Log Messages

There are four Broker log messages that may occur if flow control
through queue capacity limits is enabled. Firstly, when a capacity
limited queue becomes overfull, a log message similar to the following
is produced

    MESSAGE [vh(/test)/qu(MyQueue)] [vh(/test)/qu(MyQueue)] QUE-1003 : Overfull : Size : 1,200 bytes, Capacity : 1,000
                    

Then for each channel which becomes blocked upon the overful queue a log
message similar to the following is produced:

    MESSAGE [con:2(guest@anonymous(713889609)/test)/ch:1] [con:2(guest@anonymous(713889609)/test)/ch:1] CHN-1005 : Flow Control Enforced (Queue MyQueue)
                    

When enough messages have been consumed from the queue that it becomes
underfull, then the following log is generated:

    MESSAGE [vh(/test)/qu(MyQueue)] [vh(/test)/qu(MyQueue)] QUE-1004 : Underfull : Size : 600 bytes, Resume Capacity : 800
                    

And for every channel which becomes unblocked you will see a message
similar to:

    MESSAGE [con:2(guest@anonymous(713889609)/test)/ch:1] [con:2(guest@anonymous(713889609)/test)/ch:1] CHN-1006 : Flow Control Removed
                    

Obviously the details of connection, virtual host, queue, size,
capacity, etc would depend on the configuration in use.

### <span class="header-section-number">1.2.2</span> Disk quota-based flow control

Flow control can also be triggered when a configured disk quota is
exceeded. This is supported by the BDB and Derby virtualhosts.

This functionality blocks all producers on reaching the disk overflow
limit. When consumers consume the messages, causing disk space usage to
falls below the underflow limit, the producers are unblocked and
continue working as normal.

Two limits can be configured:

overfull limit - the maximum space on disk (in bytes).

underfull limit - when the space on disk drops below this limit,
producers are allowed to resume publishing.

The overfull and underful limit can be specified when a new virtualhost
is created or an exiting virtualhost is edited. This can be done using
the Store Overflow and Store Underfull settings within the virtual host
creation and edit dialogue. If editing an existing virtualhost, the
virtualhost must be restarted for the new values to take effect.

The disk quota functionality is based on "best effort" principle. This
means the broker cannot guarantee that the disk space limit will not be
exceeded. If several concurrent transactions are started before the
limit is reached, which collectively cause the limit to be exceeded, the
broker may allow all of them to be committed.

#### <span class="header-section-number">1.2.2.1</span> Broker Log Messages for quota flow control

There are two broker log messages that may occur if flow control through
disk quota limits is enabled. When the virtual host is blocked due to
exceeding of the disk quota limit the following message appears in the
broker log

    [vh(/test)/ms(BDBMessageStore)] MST-1008 : Store overfull, flow control will be enforced
                        

When virtual host is unblocked after cleaning the disk space the
following message appears in the broker log

    [vh(/test)/ms(BDBMessageStore)] MST-1009 : Store overfull condition cleared
                        

## <span class="header-section-number">1.3</span> Client impact and configuration

If a producer sends to a queue which is overfull, the broker will
respond by instructing the client not to send any more messages. The
impact of this is that any future attempts to send will block until the
broker rescinds the flow control order.

While blocking the client will periodically log the fact that it is
blocked waiting on flow control.

    WARN   Message send delayed by 5s due to broker enforced flow control
    WARN   Message send delayed by 10s due to broker enforced flow control
            

After a set period the send will timeout and throw a JMSException to the
calling code.

If such a JMSException is thrown, the message will not be sent to the
broker, however the underlying Session may still be active - in
particular if the Session is transactional then the current transaction
will not be automatically rolled back. Users may choose to either
attempt to resend the message, or to roll back any transactional work
and close the Session.

Both the timeout delay and the periodicity of the warning messages can
be set using Java system properties.

The amount of time (in milliseconds) to wait before timing out is
controlled by the property qpid.flow\_control\_wait\_failure.

The frequency at which the log message informing that the producer is
flow controlled is sent is controlled by the system property
qpid.flow\_control\_wait\_notify\_period.

Adding the following to the command line to start the client would
result in a timeout of one minute, with warning messages every ten
seconds:

    -Dqpid.flow_control_wait_failure=60000
    -Dqpid.flow_control_wait_notify_period=10000
            
