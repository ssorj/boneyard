# <span class="header-section-number">1</span> Producer Flow Control

## <span class="header-section-number">1.1</span> Overview

As of release 0.10, the C++ broker supports the use of flow control to
throttle back message producers that are at risk of overflowing a
destination queue.

Each queue in the C++ broker has two threshold values associated with
it:

Flow Stop Threshold: this is the level of queue resource utilization
above which flow control will be enabled. Once this threshold is
crossed, the queue is considered in danger of overflow.

Flow Resume Threshold - this is the level of queue resource utilization
below which flow control will be disabled. Once this threshold is
crossed, the queue is no longer considered in danger of overflow.

In the above description, queue resource utilization may be defined as
the total count of messages currently enqueued, or the total sum of all
message content in bytes.

The value for a queue's Flow Stop Threshold must be greater than or
equal to the value of the queue's Flow Resume Threshold.

### <span class="header-section-number">1.1.1</span> Example

Let's consider a queue with a maximum limit set on the total number of
messages that may be enqueued to that queue. Assume this maximum message
limit is 1000 messages. Assume also that the user configures a Flow Stop
Threshold of 900 messages, and a Flow Resume Threshold of 500 messages.
Then the following holds:

The queue's initial flow control state is "OFF".

While the total number of enqueued messages is less than or equal to
900, the queue's flow control state remains "OFF".

When the total number of enqueued messages is greater than 900, the
queue's flow control state transitions to "ON".

When the queue's flow control state is "ON", it remains "ON" until the
total number of enqueued messages is less than 500. At that point, the
queue's flow control state transitions to "OFF".

A similar example using total enqueued content bytes as the threshold
units are permitted.

Thresholds may be set using both total message counts and total byte
counts. In this case, the following rules apply:

1\) Flow control is "ON" when either stop threshold value is crossed.

2\) Flow control remains "ON" until both resume thresholds are satisfied.

### <span class="header-section-number">1.1.2</span> Example

Let's consider a queue with a maximum size limit of 10K bytes, and 5000
messages. A user may assign a Flow Stop Threshold based on a total
message count of 4000 messages. They may also assigne a Flow Stop
Threshold of 8K bytes. The queue's flow control state transitions to
"ON" if either threshold is crossed: (total-msgs greater-than 4000 OR
total-bytes greater-than 8K).

Assume the user has assigned Flow Resume threshold's of 3000 messages
and 6K bytes. Then the queue's flow control will remain active until
both thresholds are satified: (total-msg less-than 3000 AND total-bytes
less-than 6K).

The Broker enforces flow control by delaying the completion of the
Message.Transfer command that causes a message to be delivered to a
queue with active flow control. The completion of the Message.Transfer
command is held off until flow control state transitions to "OFF" for
all queues that are a destination for that command.

A message producing client is permitted to have a finite number of
commands pending completion. When the total number of these outstanding
commands reaches the limit, the client must not issue further commands
until one or more of the outstanding commands have completed. This
window of outstanding commands is considered the sender's "capacity".
This allows any given producer to have a "capacity's" worth of messages
blocked due to flow control before the sender must stop sending further
messages.

This capacity window must be considered when determining a suitable flow
stop threshold for a given queue, as a producer may send its capacity
worth of messages \_after\_ a queue has reached the flow stop threshold.
Therefore, a flow stop threshould should be set such that the queue can
accomodate more messages without overflowing.

For example, assume two clients, C1 and C2, are producing messages to
one particular destination queue. Assume client C1 has a configured
capacity of 50 messages, and client C2's capacity is 15 messages. In
this example, assume C1 and C2 are the only clients queuing messages to
a given queue. If this queue has a Flow Stop Threshold of 100 messages,
then, worst-case, the queue may receive up to 165 messages before
clients C1 and C2 are blocked from sending further messages. This is due
to the fact that the queue will enable flow control on receipt of its
101'st message - preventing the completion of the Message.Transfer
command that carried the 101'st message. However, C1 and C2 are allowed
to have a total of 65 (50 for C1 and 15 for C2) messages pending
completion of Message.Transfer before they will stop producing messages.
Thus, up to 65 messages may be enqueued beyond the flow stop threshold
before the producers will be blocked.

## <span class="header-section-number">1.2</span> User Interface

By default, the C++ broker assigns a queue's flow stop and flow resume
thresholds when the queue is created. The C++ broker also allows the
user to manually specify the flow control thresholds on a per queue
basis.

However, queues that have been configured with a Limit Policy of type
RING or RING-STRICT do NOT have queue flow thresholds enabled by
default. The nature of a RING queue defines its behavior when its
capacity is reach: replace the oldest message.

The flow control state of a queue can be determined by the "flowState"
boolean in the queue's QMF management object. The queue's management
object also contains a counter that increments each time flow control
becomes active for the queue.

The broker applies a threshold ratio to compute a queue's default flow
control configuration. These thresholds are expressed as a percentage of
a queue's maximum capacity. There is one value for determining the stop
threshold, and another for determining the resume threshold. The user
may configure these percentages using the following broker configuration
options:

            --default-flow-stop-threshold ("Queue capacity level at which flow control is activated.")
            --default-flow-resume-threshold ("Queue capacity level at which flow control is de-activated.")
          

For example:

            qpidd --default-flow-stop-threshold=90 --default-flow-resume-threshold=75
          

Sets the default flow stop threshold to 90% of a queue's maximum
capacity and the flow resume threshold to 75% of the maximum capacity.
If a queue is created with a default-queue-limit of 10000 bytes, then
the default flow stop threshold would be 90% of 10000 = 9000 bytes and
the flow resume threshold would be 75% of 10000 = 7500. The same
computation is performed should a queue be created with a maximum size
expressed as a message count instead of a byte count.

If not overridden by the user, the value of the
default-flow-stop-threshold is 80% and the value of the
default-flow-resume-threshold is 70%.

The user may disable default queue flow control broker-wide by
specifying the value 0 for both of these configuration options. Note
that flow control may still be applied manually on a per-queue basis in
this case.

The user may manually set the flow thresholds when creating a queue. The
following options may be provided when adding a queue using the
`qpid-config` command line tool:

            --flow-stop-size=N  Sets the queue's flow stop threshold to N total bytes.
            --flow-resume-size=N  Sets the queue's flow resume threshold to N total bytes.
            --flow-stop-count=N Sets the queue's flow stop threshold to N total messages.
            --flow-resume-count=N Sets the queue's flow resume threshold to N total messages.
          

Flow thresholds may also be specified in the `queue.declare` method, via
the `arguments` parameter map. The following keys can be provided in the
arguments map for setting flow thresholds:

| Key                      | Value                                                            |
|--------------------------|------------------------------------------------------------------|
| qpid.flow\_stop\_size    | integer - queue's flow stop threshold value in bytes             |
| qpid.flow\_resume\_size  | integer - queue's flow resume threshold value in bytes           |
| qpid.flow\_stop\_count   | integer - queue's flow stop threshold value as a message count   |
| qpid.flow\_resume\_count | integer - queue's flow resume threshold value as a message count |

The user may disable flow control on a per queue basis by setting the
flow-stop-size and flow-stop-count to zero for the queue.

The current state of flow control for a given queue can be determined by
the "flowStopped" statistic. This statistic is available in the queue's
QMF management object. The value of flowStopped is True when the queue's
capacity has exceeded the flow stop threshold. The value of flowStopped
is False when the queue is no longer blocking due to flow control.

A queue will also track the number of times flow control has been
activated. The "flowStoppedCount" statistic is incremented each time the
queue's capacity exceeds a flow stop threshold. This statistic can be
used to monitor the activity of flow control for any given queue over
time.

| Statistic Name   | Type    | Description                                               |
|------------------|---------|-----------------------------------------------------------|
| flowStopped      | Boolean | If true, producers are blocked by flow control.           |
| flowStoppedCount | count32 | Number of times flow control was activated for this queue |


