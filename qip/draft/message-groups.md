[Index](../index.html)

# Message Groups

## Status

Draft

## Summary

This document describes a new feature that would allow an application to
classify a set of related messages as belonging to a group. This document also
describes two policies that the broker could apply when delivering a message
group to one or more consumers.


## Problem

It would be useful to give an application the ability to classify a set of
messages as belonging to a single unit of work.  Furthermore, if the broker can
identify messages belonging to the same unit of work, it can enforce policies
that control how that unit of work can be consumed.

For example, it may be desirable to guarantee that a particular set of
messages are consumed by the same client, even in the case where there are
multiple clients consuming from the same queue.

In a different scenario, it may be permissible for different clients to consume
messages from the same group, as long as it can be guaranteed that the
individual messages are not processed in parallel.  In other words, the broker
would ensure that messages are processed by consumers in the same order in
which they were enqueued.

For example, assume we have a shopping application that manages items in a
virtual shopping cart.  A user may add an item to their shopping cart, then
change their mind and remove it.  If the application sends an "add" message to
the broker, immediately followed by a "remove" message, they will be queued in
the proper order - "add", then "remove".

However, if there are multiple consumers, it is possible that once a consumer
acquires the "add" message, a different consumer may acquire the "remove"
message.  This allows both messages to be processed in parallel, which could
result in the "remove" operation being performed before the "add" operation.


## Solution

This QIP proposes the following:

1) provide the ability for a message producer to designate a set of messages
as belonging to the same group.

2) allow the broker to identify messages that belong to the same group.

3) define policies for the broker that control the delivery of messages
belonging to the same group.

For #1:

The sending application would define a message header that would contain the
message's group identifier.  The group identifier stored in that header field
would be a string value determined by the application.  Messages from the same
group would have the same group identifier value.

For #2:

The key for the header that contains the group identifier would be provided to
the broker via configuration.

From the broker's perspective, the number of different group id values would be
unlimited.  And the value of group identifiers would not be provided ahead of
time by configuration: the broker must learn them at runtime.

For #3:

This QIP defines two message group policies.  Additional policies may be
defined in the future.

Policy 1: Exclusive Consumer

With this policy, the broker would guarantee that all messages in a group
would be delivered to the same client.

This policy would be configured on a per-queue basis.  When the first message
of a new message group becomes available for delivery, the broker will
associate that group with the next available consumer.  The broker would then
guarantee that all messages from that group are delivered to that consumer
only.

The broker will maintain the group/client association for the lifetime of the
client.  Should the client die or cancel its subscription, any unacknowledged
messages in the group will be assigned to a different client (preserving
message order).  Group/client associations are not maintained across broker
restart.  These associations must be replicated in a clustered broker.


Policy #2: Sequenced Consumers

With this policy, the broker would guarantee that the order in which messages
in a group are processed by consumers is the same order in which the messages
where enqueued.  This guarantee would be upheld even if the messages of the
group are processed by different consumers.  No two messages from the same
group would be processed in parallel by different consumers.

Specifically, for any given group, the broker allows only the first N messages
in the group to be available for delivery to a particular consumer.  The value
of N would be determined by the selected consumer's configured prefetch
capacity.  The broker blocks access to the remaining messages in that group by
any other consumer.  Once the selected consumer has acknowledged that first set
of delivered messages, the broker allows the next messages in the group to be
available for delivery.  The next set of messages may be delivered to a
different consumer.

This policy would be configured on a per-queue basis.  Configuration would
include designating the key of the application header that specifies the group
id.

Note will that, with this policy, the consuming application has to:

1. ensure that it has completely processed the data in a received message
before accepting that message, as described in Section 2.6.2. Transfer of
Responsibility, of the AMQP-0.10 specification.

2. ensure that messages are not selectively acknowledged or released - order
must be preserved in both cases.

Note well that in the case of either of these proposed policies, distinct
message groups would not block each other from delivery.  For example, assume a
queue contains messages from two different message groups - say group "A" and
group "B" - and they are enqueued such that "A"'s messages are in front of
"B". If the first message of group "A" is in the process of being consumed by a
client, then the remaining "A" messages are blocked, but the messages of the
"B" group are available for consumption - even though it is "behind" group "A"
in the queue.


## Rationale


The solution described above allows an application to designate a set of
related messages, and provides policies for controlling the consumption of the
message group.

 * Goal: allow dynamic values for the group identifiers (no preconfiguration of identifiers necessary)
 * Goal: the number of message groups "in flight" should only be limited by the available resources (no need to configure a hard limit).
 * Goal: manageability: visibility into the message groups currently on a given queue
 * Goal: manageability: purge, move, reroute messages at the group level.

## Implementation Notes

 * Queues: support configuration of the group identifier header key.
 * Messages: provide access to group identifier.
 * Queues: identify head message of next available message group.
 * Queues: block the trailing messages in a given message group from being consumed.
 * Consumers: track the message group of the currently acquired message(s).
 * Clustering: ensure state is replicated within the cluster as needed.

## Consequences

 * __Development:__ No changes to the development process.
 * __Release:__ No changes to the release process.
 * __Documentation:__ User documentation will be needed to explain the feature, and the steps to configure and manage the new feature.
 * __Configuration:__ Yes: per-queue group identifier header key is configurable.  Queue state with regard to in-flight message groups needs to be visible.  Additional methods to purge/move/reroute a message group.
 * __Compatibility:__ Unlikely - new feature that would need to be enabled manually.  Applications wishing to use the feature would need to implement a message grouping policy, and ensure the processing of received message data is compliant with the desired policy.

## References

 * None.

## Contributor-in-Charge

Kenneth Giusti, <kgiusti@redhat.com>

## Contributors

 * Ted Ross, <tross@redhat.com>

## Version

0.2
