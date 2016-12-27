# <span class="header-section-number">1</span> Handing Undeliverable Messages

## <span class="header-section-number">1.1</span> Introduction

Messages that cannot be delivered successfully to a consumer (for
instance, because the client is using a transacted session and
rolls-back the transaction) can be made available on the queue again and
then subsequently be redelivered, depending on the precise session
acknowledgement mode and messaging model used by the application. This
is normally desirable behaviour that contributes to the ability of a
system to withstand unexpected errors. However, it leaves open the
possibility for a message to be repeatedly redelivered (potentially
indefinitely), consuming system resources and preventing the delivery of
other messages. Such undeliverable messages are sometimes known as
poison messages.

For an example, consider a stock ticker application that has been
designed to consume prices contained within JMS TextMessages. What if
inadvertently a BytesMessage is placed onto the queue? As the ticker
application does not expect the BytesMessage, its processing might fail
and cause it to roll-back the transaction, however the default behavior
of the Broker would mean that the BytesMessage would be delivered over
and over again, preventing the delivery of other legitimate messages,
until an operator intervenes and removes the erroneous message from the
queue.

Qpid has maximum delivery count and dead-letter queue (DLQ) features
which can be used in concert to construct a system that automatically
handles such a condition. These features are described in the following
sections.

## <span class="header-section-number">1.2</span> Maximum Delivery Count

Maximum delivery count is a property of a queue. If a consumer
application is unable to process a message more than the specified
number of times, then the broker will either route the message to a
dead-letter queue (if one has been defined), or will discard the
message.

In order for a maximum delivery count to be enforced, the consuming
client *must* call
[Session\#rollback()](&oracleJeeDocUrl;javax/jms/Session.html#rollback())
(or
[Session\#recover()](&oracleJeeDocUrl;javax/jms/Session.html#recover())
if the session is not transacted). It is during the Broker's processing
of Session\#rollback() (or Session\#recover()) that if a message has
been seen at least the maximum number of times then it will move the
message to the DLQ or discard the message.

If the consuming client fails in another manner, for instance, closes
the connection, the message will not be re-routed and consumer
application will see the same poison message again once it reconnects.

If the consuming application is using AMQP 0-9-1, 0-9, or 0-8 protocols,
it is necessary to set the client system property
`qpid.reject.behaviour` or connection or binding URL option
`rejectbehaviour` to the value `server`.

It is possible to determine the number of times a message has been sent
to a consumer via the Management interfaces, but is not possible to
determine this information from a message client. Specifically, the
optional JMS message header JMSXDeliveryCount is not supported.

Maximum Delivery Count can be specified when a new queue is created or
using the the queue declare property x-qpid-maximum-delivery-count

## <span class="header-section-number">1.3</span> Dead Letter Queues (DLQ)

A Dead Letter Queue (DLQ) acts as an destination for messages that have
somehow exceeded the normal bounds of processing and is utilised to
prevent disruption to flow of other messages. When a DLQ is enabled for
a given queue if a consuming client indicates it no longer wishes the
receive the message (typically by exceeding a Maximum Delivery Count)
then the message is moved onto the DLQ and removed from the original
queue.

The DLQ feature causes generation of a Dead Letter Exchange and a Dead
Letter Queue. These are named convention QueueName*\_DLE* and
QueueName*\_DLQ*.

DLQs can be enabled when a new queue is created or using the queue
declare property x-qpid-dlq-enabled.

> **Caution**
>
> Applications making use of DLQs *should* make provision for the
> frequent examination of messages arriving on DLQs so that both
> corrective actions can be taken to resolve the underlying cause and
> organise for their timely removal from the DLQ. Messages on DLQs
> consume system resources in the same manner as messages on normal
> queues so excessive queue depths should not be permitted to develop.
