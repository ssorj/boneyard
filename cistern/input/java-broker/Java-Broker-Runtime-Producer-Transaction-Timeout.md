# <span class="header-section-number">1</span> Producer Transaction Timeout

## <span class="header-section-number">1.1</span> General Information

The transaction timeout mechanism is used to control broker resources
when clients producing messages using transactional sessions hang or
otherwise become unresponsive, or simply begin a transaction and keep
using it without ever calling
[Session\#commit()](&oracleJeeDocUrl;javax/jms/Session.html#commit).

Users can choose to configure an idleWarn or openWarn threshold, after
which the identified transaction should be logged as a WARN level alert
as well as (more importantly) an idleClose or openClose threshold after
which the transaction and the connection it applies to will be closed.

This feature is particularly useful in environments where the owner of
the broker does not have full control over the implementation of
clients, such as in a shared services deployment.

The following section provide more details on this feature and its use.

## <span class="header-section-number">1.2</span> Purpose

This feature has been introduced to address the scenario where an open
transaction on the broker holds an open transaction on the persistent
store. This can have undesirable consequences if the store does not time
out or close long-running transactions, such as with BDB. This can can
result in a rapid increase in disk usage size, bounded only by available
space, due to growth of the transaction log.

## <span class="header-section-number">1.3</span> Scope

Note that only
[MessageProducer](&oracleJeeDocUrl;javax/jms/MessageProducer.html)
clients will be affected by a transaction timeout, since store
transaction lifespan on a consumer only spans the execution of the call
to Session\#commit() and there is no scope for a long-lived transaction
to arise.

It is also important to note that the transaction timeout mechanism is
purely a JMS transaction timeout, and unrelated to any other timeouts in
the Qpid client library and will have no impact on any RDBMS your
application may utilise.

## <span class="header-section-number">1.4</span> Effect

Full details of configuration options are provided in the sections that
follow. This section gives a brief overview of what the Transaction
Timeout feature can do.

### <span class="header-section-number">1.4.1</span> Broker Logging and Connection Close

When the openWarn or idleWarn specified threshold is exceeded, the
broker will log a WARN level alert with details of the connection and
channel on which the threshold has been exceeded, along with the age of
the transaction.

When the openClose or idleClose specified threshold value is exceeded,
the broker will throw an exception back to the client connection via the
[ExceptionListener](&oracleJeeDocUrl;javax/jms/ExceptionListener.html),
log the action and then close the connection.

The example broker log output shown below is where the idleWarn
threshold specified is lower than the idleClose threshold and the broker
therefore logs the idle transaction 3 times before the close threshold
is triggered and the connection closed out.

    CHN-1008 : Idle Transaction : 13,116 ms
    CHN-1008 : Idle Transaction : 14,116 ms
    CHN-1008 : Idle Transaction : 15,118 ms
    CHN-1003 : Close
       

The second example broker log output shown below illustrates the same
mechanism operating on an open transaction.

    CHN-1007 : Open Transaction : 12,406 ms
    CHN-1007 : Open Transaction : 13,406 ms
    CHN-1007 : Open Transaction : 14,406 ms
    CHN-1003 : Close
       

### <span class="header-section-number">1.4.2</span> Client Side Effect

After a Close threshold has been exceeded, the trigger client will
receive this exception on its [exception
listener](&oracleJeeDocUrl;javax/jms/ExceptionListener.html), prior to
being disconnected:

org.apache.qpid.AMQConnectionClosedException: Error: Idle transaction
timed out [error code 506: resource error]

Any later attempt to use the connection will result in this exception
being thrown:

    Producer: Caught an Exception: javax.jms.IllegalStateException: Object org.apache.qpid.client.AMQSession_0_8@129b0e1 has been closed
        javax.jms.IllegalStateException: Object org.apache.qpid.client.AMQSession_0_8@129b0e1 has been closed
        at org.apache.qpid.client.Closeable.checkNotClosed(Closeable.java:70)
        at org.apache.qpid.client.AMQSession.checkNotClosed(AMQSession.java:555)
        at org.apache.qpid.client.AMQSession.createBytesMessage(AMQSession.java:573)
       

Thus clients must be able to handle this case successfully, reconnecting
where required and registering an exception listener on all connections.
This is critical, and must be communicated to client applications by any
broker owner switching on transaction timeouts.

## <span class="header-section-number">1.5</span> Configuration

### <span class="header-section-number">1.5.1</span> Configuration

The transaction timeouts can be specified when a new virtualhost is
created or an exiting virtualhost is edited.

We would recommend that only warnings are configured at first, which
should allow broker administrators to obtain an idea of the distribution
of transaction lengths on their systems, and configure production
settings appropriately for both warning and closure. Ideally
establishing thresholds should be achieved in a representative UAT
environment, with clients and broker running, prior to any production
deployment.

It is impossible to give suggested values, due to the large variation in
usage depending on the applications using a broker. However, clearly
transactions should not span the expected lifetime of any client
application as this would indicate a hung client.

When configuring warning and closure timeouts, it should be noted that
these only apply to message producers that are connected to the broker,
but that a timeout will cause the connection to be closed - this
disconnecting all producers and consumers created on that connection.

This should not be an issue for environments using Mule or Spring, where
connection factories can be configured appropriately to manage a single
MessageProducer object per JMS Session and Connection. Clients that use
the JMS API directly should be aware that sessions managing both
consumers and producers, or multiple producers, will be affected by a
single producer hanging or leaving a transaction idle or open, and
closed, and must take appropriate action to handle that scenario.
