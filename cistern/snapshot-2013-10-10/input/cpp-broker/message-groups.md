# Message Groups

[Up to Queues](queues.html)

## Overview

The broker allows messaging applications to classify a set of related
messages as belonging to a group. This allows a message producer to
indicate to the consumer that a group of messages should be considered a
single logical operation with respect to the application.

The broker can use this group identification to enforce policies
controlling how messages from a given group can be distributed to
consumers. For instance, the broker can be configured to guarantee all
the messages from a particular group are processed in order across
multiple consumers.

For example, assume we have a shopping application that manages items in
a virtual shopping cart. A user may add an item to their shopping cart,
then change their mind and remove it. If the application sends an *add*
message to the broker, immediately followed by a *remove* message, they
will be queued in the proper order - *add*, followed by *remove*.

However, if there are multiple consumers, it is possible that once a
consumer acquires the *add* message, a different consumer may acquire
the *remove* message. This allows both messages to be processed in
parallel, which could result in a "race" where the *remove* operation is
incorrectly performed before the *add* operation.

## Grouping Messages

In order to group messages, the application would designate a particular
message header as containing a message's *group identifier*. The group
identifier stored in that header field would be a string value set by
the message producer. Messages from the same group would have the same
group identifier value. The key that identifies the header must also be
known to the message consumers. This allows the consumers to determine a
message's assigned group.

The header that is used to hold the group identifier, as well as the
values used as group identifiers, are totally under control of the
application.

## The Role of the Broker

The broker will apply the following processing on each grouped message:

-   Enqueue a received message on the destination queue.
-   Determine the message's group by examining the message's group
    identifier header.
-   Enforce
    consumption ordering
    among messages belonging to the same group.

*Consumption ordering* means that the broker will not allow outstanding
unacknowledged messages to *more than one consumer for a given group*.

This means that only one consumer can be processing messages from a
particular group at a given time. When the consumer acknowledges all of
its acquired messages, then the broker *may* pass the next pending
message from that group to a different consumer.

Specifically, for any given group the broker allows only the first N
messages in the group to be delivered to a consumer. The value of N
would be determined by the selected consumer's configured prefetch
capacity. The broker blocks access by any other consumer to any
remaining undelivered messages in that group. Once the receiving
consumer has:

-   acknowledged,
-   released, or
-   rejected

all the delivered messages, the broker allows the next messages in the
group to be delivered. The next messages *may* be delivered to a
different consumer.

Note well that distinct message groups would not block each other from
delivery. For example, assume a queue contains messages from two
different message groups - say group "A" and group "B" - and they are
enqueued such that "A"'s messages are in front of "B". If the first
message of group "A" is in the process of being consumed by a client,
then the remaining "A" messages are blocked, but the messages of the "B"
group are available for consumption by other consumers - even though it
is "behind" group "A" in the queue.

## Well Behaved Consumers

The broker can only enforce policy when delivering messages. To
guarantee that strict message ordering is preserved, the consuming
application must adhere to the following rules:

-   completely process the data in a received message before accepting
    that message
-   acknowledge (or reject) messages in the same order as they are
    received
-   avoid releasing messages (see below)

The term *processed* means that the consumer has finished updating all
application state affected by the message that has been received. See
section 2.6.2. Transfer of Responsibility, of the AMQP-0.10
specification for more detail.

> **Note**
>
> If a consumer does not adhere to the above rules, it may affect the
> ordering of grouped messages even when the broker is enforcing
> consumption order. This can be done by selectively acknowledging and
> releasing messages from the same group.
>
> Assume a consumer has received two messages from group "A", "A-1" and
> "A-2", in that order. If the consumer releases "A-1" then acknowledges
> "A-2", "A-1" will be put back onto the queue and "A-2" will be removed
> from the queue. This allows another consumer to acquire and process
> "A-1" *after* "A-2" has been processed.
>
> Under some application-defined circumstances, this may be acceptable
> behavior. However, if order must be preserved, the client should
> either release *all* currently held messages, or discard the target
> message using reject.

## Broker Configuration

In order for the broker to determine a message's group, the key for the
header that contains the group identifier must be provided to the broker
via configuration. This is done on a per-queue basis, when the queue is
first configured.

This means that message group classification is determined by the
message's destination queue.

Specifically, the queue "holds" the header key that is used to find the
message's group identifier. All messages arriving at the queue are
expected to use the same header key for holding the identifer. Once the
message is enqueued, the broker looks up the group identifier in the
message's header, and classifies the message by its group.

Message group support can be enabled on a queue using the `qpid-config`
command line tool. The following options should be provided when adding
a new queue:

  Option                       Description
  ---------------------------- ------------------------------------------------------------------------------------------------------------------
  --group-header=header-name   Enable message group support for this queue. Specify name of application header that holds the group identifier.
  --shared-groups              Enforce ordered message group consumption across multiple consumers.

  : qpid-config options for creating message group queues

Message group support may also be specified in the `queue.declare`
method via the `arguments` parameter map, or using the messaging address
syntax. The following keys must be provided in the arguments map to
enable message group support on a queue:

  Key                       Value
  ------------------------- -----------------------------------------------------------------------
  qpid.group\_header\_key   string - key for message header that holds the group identifier value
  qpid.shared\_msg\_group   1 - enforce ordering across multiple consumers

  : Queue Declare/Address Syntax Message Group Configuration Arguments

It is important to note that there is no need to provide the actual
group identifer values that will be used. The broker learns this values
as messages are recieved. Also, there is no practical limit - aside from
resource limitations - to the number of different groups that the broker
can track at run time.

> **Note**
>
> Message grouping is not supported on LVQ or Priority queues.

This example uses the qpid-config tool to create a message group queue
called "MyMsgQueue". The message header that contains the group
identifier will use the key "GROUP\_KEY".

    qpid-config add queue MyMsgQueue --group-header="GROUP_KEY" --shared-groups
            

This example uses the messaging address syntax to create a message group
queue with the same configuration as the previous example.

    sender = session.createSender("MyMsgQueue;"
                                  " {create:always, delete:receiver,"
                                  " node: {x-declare: {arguments:"
                                  " {'qpid.group_header_key':'GROUP_KEY',"
                                  " 'qpid.shared_msg_group':1}}}}")
            

### Default Group

Should a message without a group identifier arrive at a queue configured
for message grouping, the broker assigns the message to the default
group. Therefore, all such "unidentified" messages are considered by the
broker as part of the same group. The name of the default group is
`"qpid.no-group"`. This default can be overridden by suppling a
different value to the broker configuration item
`"default-message-group"`:

    qpidd --default-msg-group "EMPTY-GROUP"
                
