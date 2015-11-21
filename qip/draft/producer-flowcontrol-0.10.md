[Index](../index.html)

# Producer throttling (flow control) for AMQP 0-10

## Status

Draft

## Summary

The C++ broker needs to be able to limit the flow of inbound messages
when available queue resources become low.  This document describes an
enhancement to the C++ broker that will provide this ability.

## Problem

In the current C++ broker/client implementation, when a queue on the
broker fills to the point where it cannot accept any more messages
(`--default-queue-limit` hit), the broker will forcibly disconnect any
client that attempts to route a message to that queue. This is an
abrupt failure - the producing client is not privy to the queue's
remaining capacity. The broker provides no feedback to the producing
client, which could be used to throttle the client's message
production rate.

This proposed feature will provide a mechanism to allow the C++ broker
to limit a client's (producer's) message input based on available
queue resources.

## Solution

The solution is based on the concept of delaying the completion of a
message transfer until resources become available on the broker.

Specifically, a sending client will maintain a window of outstanding
message transfers.  This is a set of message transfers that have not
yet been completed by the broker.  Once this window fills, the sending
client must not issue further message transfers until one or more
pending transfers are completed by the broker.  The broker, in turn,
will not complete a message transfer if one or more of the destination
queues are in a low resource state.  Once resources become available
on all of the destination queues for a particular message, the broker
will complete that message's transfer.

In summary, clients may have a fixed window of outstanding messages,
and the broker determines the rate at which the window moves.  This
rate is dependent upon the resources available to the queues that are
the destinations of the messages.

## Rationale

The upcoming AMQP 1.0 protocol addresses producer flow control
directly at the protocol level and a full solution will be implemented
as part of the work to implement AMQP 1.0.  However, there is a real need
for some level of producer flow control in the short term - simply
disconnecting the client as done today is not acceptable.  This
proposal can deliver a limited solution using the existing AMQP 0-10
implementation in the short term.

It must be noted that the AMQP 0-10 protocol provides a credit based
flow control mechanism for subscribers. While this could in theory be
used for producers, the protocol does not explicitly cover that use
case, and there is no standard or obvious way of utilising it.

 * Goal: permit the broker's connection to a sender to survive a temporary high-load message output scenario (i.e. "bursty producer'). 
 * Nongoal: solve the "slow consumer" problem: a "slow consumer" is a pathological scenario  where a receiver's consumption rate is on-average less than the senders'  production rate.  At some point, resources will run out and the sender  will be disconnected, as is done by the current implementation.
 * Goal: perform head-of-line blocking based on the current message's destination.
 * Nongoal: predictive flow control per individual message's destination (i.e. allow messages addressed to a unsaturated destination "skip" message that are flow controlled.)
 * Goal: queue watermarks should be configurable, and allow run-time modification
 * Goal: the C++ broker's user-visible configuration interface will be consistent with the Java Broker's implementation of flow control.  Refer to: https://cwiki.apache.org/qpid/use-producer-flow-control.html
 * Nongoal: provide flow control to those clients which do not support the new fixed window + completion concept.
 * Goal: existing clients which do not support this feature will continue to operate in the current manner (no flow control).

## Implementation Notes

 * Queues: support configurable high and low watermarks, configurable per queue.  Sane defaults.
 * Queues: support a boolean "saturated" flag - indicates if the queue is under resource pressure.
 * Session state: maintain flow control state per producer (already part of session state).
 * Messages: maintain a "pending completion" counter.
 * Clients: support a window of outstanding message transfers that have not been completed

Use the queue's watermarks and state, along with the per-message
counter, to determine when a received message can be completed:

On enqueue:

>  Enqueue the message to a destination queue.  If, after the enqueue,
>  the amount of queue resources become greater than the high
>  watermark, set the saturated flag.  If the saturated flag is set,
>  do not complete the message transfer.  Instead, increment the
>  pending completion counter in the message.  The queue will maintain
>  a list of messages that are pending completion of their message
>  transfers.

On dequeue:

>  Dequeue the message.  If the amount of queue resources then drops
>  below the low water mark, clear the saturated flag.  Once the
>  saturated flag is cleared, pending messages should have their
>  pending completion counter decremented.  Any messages with a zero
>  pending completion counter should have their corresponding
>  message.transfer command completed.  If the queue is still
>  saturated after the message has been dequeued, and the message's
>  transfer has not been completed, decrement the pending completion
>  counter anyways.

## Consequences

 * __Development:__ No changes to the development process.
 * __Release:__ No changes to the release process.
 * __Documentation:__ User documentation will be needed to explain configuring the queue watermarks.
 * __Configuration:__ Yes - queue watermarks must be configurable.  Queue state needs to be visible.
     deployed?*
 * __Compatibility:__ Unlikely.

## References

 * [QPID-2935](https://issues.apache.org/jira/browse/QPID-2935)

## Contributor-in-Charge

Kenneth Giusti, <kgiusti@apache.org>

## Contributors

 * Alan Conway, <aconway@redhat.com>
 * Gordon Sim, <gsim@redhat.com>
 * Rafi Schloming, <rhs@apache.org>

## Version

0.1
