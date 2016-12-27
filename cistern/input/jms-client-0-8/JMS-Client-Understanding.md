# <span class="header-section-number">1</span> Understanding the Qpid JMS client

# <span class="header-section-number">2</span> Overview

The Qpid JMS client provides a JMS 1.1 compliant implementation. As
such, the primary source of documentation is the [JMS
specification](&oracleJmsSpec;) and the [JMS
javadocs](&oracleJeeDocUrl;/javax/jms/package-summary.html). This
documentation assumes the reader has familiarity with these resources.

The remainder of this section describes how the Qpid JMS client behaves
and the effect(s) making JMS method calls will have on the Broker.

There areas where the Qpid JMS client provides features beyond those
required for JMS compliance. These are described in the sections that
follow.

These sections are also used to bring out differences that may surprise
those moving from JMS implementations provided by other vendors.

![Architecture of a typical JMS application](images/QpidJmsOverview.png)

# <span class="header-section-number">3</span> ConnectionFactory

A [ConnectionFactory](&oracleJeeDocUrl;javax/jms/ConnectionFactory.html)
allows an application to create a
[Connection](&oracleJeeDocUrl;javax/jms/Connection.html).

The application obtains the ConnectionFactory from an
[InitialContext](&oracleJdkDocUrl;javax/naming/InitialContext.html). The
InitialContext is itself obtained from an InitialContextFactory.

The Qpid JMS client provides a single implementation of the
InitialContextFactory in class
`org.apache.qpid.jndi.PropertiesFileInitialContextFactory`. This
implementation is backed by a
[Properties](&oracleJdkDocUrl;java/util/Properties.html) object which
can of course be loaded from an external properties file, or created
programatically.

The examples in the previous chapter illustrated the Java code required
to [create the InitialContext](#JMS-Client-0-8-Examples-PTP) and an
[example properties file](#JMS-Client-0-8-Examples-PTP-PropertiesFile).

The Qpid JMS client also provides an alternate connection factory
implementation providing a connection pool. This can be useful when
utilsing frameworks such as Spring. ?.

![JNDI overview](images/JndiOverview.png)

Note that the Qpid Broker does not present a JNDI interface to the
application.

# <span class="header-section-number">4</span> Connection

A Connection represents an open communication channel between
application and Broker.

Connections are created from the ConnectionFactory <span
id="fnref1">[^1^](#fn1)</span>.

Each connection utilises a single TCP/IP connection between the process
of the application and the process of the Broker. The act of
establishing a connection is therefore a relatively expensive operation.
It is recommended that the same connection is used for a series of
message interactions. Patterns utilising a connection per message should
not be used.

The underlying TCP/IP connection remains open for the lifetime of the
JMS connection. It is closed when the application calls
[Connection\#close()](&oracleJeeDocUrl;javax/jms/Connection.html#close()),
but it can also be closed if the connection is closed from the Broker
side (via a Management operation or broker shutdown or running into
conditions which AMQP specifications treats as errors and mandates
closing the connection). The JMS connection will also be closed if the
underlying TCP/IP connection is broken.

Qpid connections have failover and heartbeating capabilities. They
support SSL and client-auth. These are described in the sub-sections
that follow.

## <span class="header-section-number">4.1</span> Failover

Qpid connections support a failover feature. This is the ability to
automatically re-establish a failed connection, either to the same
Broker, or the next Broker in the broker list.

This failover process is done in a manner that is mostly transparent to
the application. After a successful failover, any existing Connection,
Session, MessageConsumer and MessageProducer objects held by the
application remain valid.

If a failover occurs during the scope of a JMS Transaction, any work
performed by that transaction is lost. The application is made aware of
this loss by way of the
[TransactionRolledBackException](&oracleJeeDocUrl;javax/jms/TransactionRolledBackException.html)
from the
[Session\#commit()](&oracleJeeDocUrl;javax/jms/Session.html#commit)
call. Applications utilising failover must be prepared to catch this
exception and respond by either repeating the work of the transaction,
or by propagating a rollback to the originating system.

If, after all retries are exhausted, failover has failed to reconnect
the application, the Connection's
[ExceptionListener](&oracleJeeDocUrl;javax/jms/ExceptionListener.html)
will receive a JMSException with a linked exception of
[AMQDisconnectedException](JMS-Client-0-8-Appendix-Exceptions-AMQDisconnectedException).
Any further use of the JMS objects (Connection, Session etc), will
results in a
[IllegalStateException](&oracleJeeDocUrl;javax/jms/IllegalStateException.html).

Configure failover using the Connection URL. Here's an example
Connection URL utilising failover between two brokers. Note the use of
the broker options
[`retries`](#JMS-Client-0-8-Connection-URL-BrokerOptions-Retries) and
[`connectdelay`](#JMS-Client-0-8-Connection-URL-BrokerOptions-ConnectDelay)
to control the number of connection attempts to each individual broker,
and the delay between each connection attempt. Also note the use of the
*failover option* `cyclecount` to control the number of times the
failover mechanism will traverse the brokerlist.

    amqp://username:password@clientid/test
                ?brokerlist='tcp://localhost:15672?retries='10'&connectdelay='1000';tcp://localhost:25672?retries='10'&connectdelay='1000''
                &failover='roundrobin?cyclecount='20''
            

For full details see ?

> **Note**
>
> Note, that a single broker failover is enabled by default. If the
> failover behaviour is not desired it can be switched off by setting a
> failover option to `nofailover` as in the example below
>
>     amqp://username:password@clientid/test
>                 ?brokerlist='tcp://localhost:15672?failover='nofailover'
>             

## <span class="header-section-number">4.2</span> Heartbeating

Qpid connections support heartbeating. When enabled, the Qpid JMS client
and Broker exchange a heartbeat during periods of inactivity. This
allows both peers to discover if the TCP/IP connection becomes
inoperable in a timely manner.

This feature is sometimes useful in applications that must traverse
firewalls as the heartbeat prevents connections from being closed during
periods when there is no application traffic.

It is also allows the both the JMS client and the Broker to confirm that
the other is *minimally* responsive. (It does nothing however to
determine the health of the higher level tiers of application, for this
reason, applications may implement an application level heartbeat either
in addition to, or instead of the heartbeat.

If the client ever fails to receive two consecutive heartbeats, the
Connection will be automatically closed and the Connection's
[ExceptionListener](&oracleJeeDocUrl;javax/jms/ExceptionListener.html)
will receive a JMSException with a linked exception of
AMQDisconnectedException. Any further use of the JMS objects
(Connection, Session etc), will results in a
[IllegalStateException](&oracleJeeDocUrl;javax/jms/IllegalStateException.html).

To enable heartbeating either use a Connection URL including the broker
option
[`heartbeat`](#JMS-Client-0-8-Connection-URL-BrokerOptions-Heartbeat),
or use the system property
[`qpid.heartbeat`](#JMS-Client-0-8-System-Properties-Heartbeat).

    amqp://guest:guest@clientid/?brokerlist='localhost:5672?heartbeat='5''
            

## <span class="header-section-number">4.3</span> SSL

The Qpid JMS client supports connections encrypted using Secure Socket
Layer (SSL) and SSL-Client Authentication. SSL is configured using
Connection URL. To use SSL, SSL must be be configured on the Broker.

Some example Connection URLs using SSL follow:

-   Simple SSL when the Broker is secured by a certificate that is
    signed by a CA which is trusted by the JVM.

        amqp://guest:guest@clientid/?brokerlist='localhost:5671'&ssl='true'
                    

-   SSL when the Broker is secured by a certificate that is signed by a
    CA which is NOT trusted by the JVM (such as when a organisation is
    using a private CA, or self-signed certificates are in use). For
    this case, we use
    [`trust_store`](#JMS-Client-0-8-Connection-URL-BrokerOptions-TrustStore)
    and
    [`trust_store_password`](#JMS-Client-0-8-Connection-URL-BrokerOptions-TrustStorePassword)
    to specify a path a truststore file (containing the certificate of
    the private-CA) and the truststore password.

        amqp://guest:guest@clientid/?brokerlist='localhost:5671?trust_store='/path/to/acme_org_ca.ts'&trust_store_password='secret''&ssl='true'
                    

-   SSL with SSL client-auth. For this case, we use
    [`key_store`](#JMS-Client-0-8-Connection-URL-BrokerOptions-KeyStore)
    and
    [`key_store_password`](#JMS-Client-0-8-Connection-URL-BrokerOptions-KeyStorePassword)
    to specify a path a keystore file (containing the certificate of the
    client) and the keystore password.

        amqp://guest:guest@clientid/?brokerlist='localhost:5671?key_store='/path/to/app1_client_cert.ks'&key_store_password='secret''&ssl='true'
                    

    Alternatively we can use
    [`client_cert_path`](#JMS-Client-0-8-Connection-URL-BrokerOptions-ClientCertPath)
    and
    [`client_cert_priv_key_ath`](#JMS-Client-0-8-Connection-URL-BrokerOptions-ClientCertPrivKeyPath)
    to specify a path to a certificate file (in PEM or DER format) and
    the private key information (again in either PEM or DER format)
    respectively.

        amqp://guest:guest@clientid/?brokerlist='localhost:5671?client_cert_path='/path/to/app1_client.crt'&client_cert_priv_key_path='/path/to/app1_client.key''&ssl='true'
                    

## <span class="header-section-number">4.4</span> Message Compression

The client has the ability to transparently compress message payloads on
outgoing messages and decompress them on incoming messages. In some
environments and with some payloads this feature might offer performance
improvements by reducing the number of bytes transmitted over the
connection.

In order to make use of message compression, the Broker must enable the
feature too, otherwise the compression options will be ignored.

To enable message compression on the client use the connection url
property
[`compressMessages`](#JMS-Client-0-8-Connection-URL-ConnectionOptions-CompressMessages)
(or JVM wide using the system property
[`qpid.connection_compress_messages`](#JMS-Client-0-8-System-Properties-ConnectionCompressMessages))

It is also possible to control the threshold at which the client will
begin to compress message payloads. See connection url property
[`messageCompressionThresholdSize`](#JMS-Client-0-8-Connection-URL-ConnectionOptions-MessageCompressionThresholdSize)
(or JVM wide using the system property
[`qpid.message_compression_threshold_size`](#JMS-Client-0-8-System-Properties-MessageCompressionThresholdSize))

> **Note**
>
> The Broker, where necessary, takes care of compressing/decompressing
> messages of the fly so that clients using message compression can
> exchange messages with clients not supporting message compression
> transparently, without application intervention.

# <span class="header-section-number">5</span> Session

A Session object is a single-threaded context for producing and
consuming messages.

Session objects are created from the Connection. Whilst Session objects
are relatively lightweight, patterns utilising a single Session per
message are not recommended.

The number of sessions open per connection at any one time is limited.
This value is negotiated when the connection is made. It defaults to
256.

Qpid JMS Sessions have the ability to prefetch messages to improve
consumer performance. This feature is described next.

## <span class="header-section-number">5.1</span> Prefetch

Prefetch specifies how many messages the client will optimistically
cache for delivery to a consumer. This is a useful parameter to tune
that can improve the throughput of an application. The prefetch buffer
is scoped per *Session*.

The size of the prefetch buffer can be tuned per Connection using the
connection url option
[`maxprefetch`](#JMS-Client-0-8-Connection-URL-ConnectionOptions-Maxprefetch)
(or JVM wide using the system property
[`max_prefetch`](#JMS-Client-0-8-System-Properties-Maxprefetch)). By
default, prefetch defaults to 500.

There are situations when you may wish to consider reducing the size of
prefetch:

1.  When using a [Competing
    Consumers](http://www.eaipatterns.com/CompetingConsumers.html)
    pattern, prefetch can give the appearance of unequal division of
    work. This will be apparent on startup when the queue has messages.
    The first consumer started will cache prefetch size number of
    messages, possibly leaving the other consumers with no initial work.

2.  When using special queue types (such as LVQs, Sorted Queue and
    Priority Queues). For these queue types the special delivery rules
    apply whilst the message resides on the Broker. As soon as the
    message is sent to the client it delivery order is then fixed. For
    example, if using a priority queue, and a prefetch of 100, and 100
    messages arrive with priority 2, the broker will send these to the
    client. If then a new message arrives with priority 1, the broker
    cannot leap frog messages of the lower priority. The priority 1
    message will be delivered at the front of the next batch.

3.  When message size is large and you do not wish the memory footprint
    of the application to grow (or suffer an OutOfMemoryError).

Finally, if using multiple MessageConsumers on a single Session, keep in
mind that unless you keep polling *all* consumers, it is possible for
some traffic patterns to result in consumer starvation and an
application level deadlock. For example, if prefetch is 100, and 100
hundred messages arrive suitable for consumer A, those messages will be
prefetched by the session, entirely filling the prefetch buffer. Now if
the application performs a blocking
[MessageConsumer\#receive()](&oracleJeeDocUrl;javax/jms/MessageConsumer.html#receive())
for Consumer B on the same Session, the application will hang
indefinitely as even if messages suitable for B arrive at the Broker.
Those messages can never be sent to the Session as no space is available
in prefetch.

> **Note**
>
> Please note, when the acknowledgement mode
> *Session\#SESSION\_TRANSACTED* or *Session\#CLIENT\_ACKNOWLEDGE* is
> set on a consuming session, the prefetched messages are released from
> the prefetch buffer on transaction commit/rollback (in case of
> acknowledgement mode *Session\#SESSION\_TRANSACTED* ) or
> acknowledgement of the messages receipt (in case of acknowledgement
> mode *Session\#CLIENT\_ACKNOWLEDGE* ). If the consuming application
> does not commit/rollback the receiving transaction (for example, due
> to mistakes in application exception handling logic), the prefetched
> messages continue to remain in the prefetch buffer preventing the
> delivery of the following messages. As result, the application might
> stop the receiving of the messages until the transaction is
> committed/rolled back (for *Session\#SESSION\_TRANSACTED* ) or
> received messages are acknowledged (for
> *Session\#CLIENT\_ACKNOWLEDGE*).

Settings maxprefetch to 0 ( either globally via JVM system property
[`max_prefetch`](#JMS-Client-0-8-System-Properties-Maxprefetch) or on a
connection level as a connection option
[`maxprefetch`](#JMS-Client-0-8-Connection-URL-ConnectionOptions-Maxprefetch)
) switches off the pre-fetching functionality. With maxprefetch=0
messages are fetched one by one without caching on the client.

> **Note**
>
> Setting maxprefetch to 0 is recommended in Spring-JMS based
> applications whenever *DefaultMassgeListenerContainer* is configured
> with a *CachingConnectionFactory* that has *cacheLevel* set to either
> *CACHE\_CONSUMER* or *CACHE\_SESSION*. In these configurations the
> Qpid JMS *Session* objects remain open in Spring's dynamically scaled
> pools. If maxprefetch is not 0, any prefetched messages held by the
> *Session* and any new ones subsequently sent to it (in the background
> until prefetch is reached) will be effectively by 'stuck' (unavailable
> to the application) until Spring decides to utilise the cached Session
> again. This can give the impression that message delivery has stopped
> even though messages remain of the queue. Setting maxprefetch to 0
> prevents this problem from occurring.
>
> If using maxprefetch \> 0 *SingleConnectionFactory* must be used.
> SingleConnectionFactory does not have the same session/consumer
> caching behaviour so does not exhibit the same problem.

## <span class="header-section-number">5.2</span> TemporaryQueues

Qpid implements JMS temporary queues as AMQP auto-delete queues. The
life cycle of these queues deviates from the JMS specification.

AMQP auto-delete queues are deleted either when the *last* Consumer
closes, or the Connection is closed. If no Consumer is ever attached to
the queue, the queue will remain until the Connection is closed.

This deviation has no practical impact on the implementation of the
[request/reply messaging
pattern](http://www.eaipatterns.com/RequestReply.html) utilising a
per-request temporary reply queue. The reply to queue is deleted as the
application closes the Consumer awaiting the response.

Temporary queues are exposed to Management in the same way as normal
queues. Temporary queue names take the form string `TempQueue` followed
by a random UUID.

Note that
[TemporaryQueue\#delete()](&oracleJeeDocUrl;javax/jms/TemporaryQueue.html#delete())
merely marks the queue as deleted on within the JMS client (and prevents
further use of the queue from the application), however, the Queue will
remain on the Broker until the Consumer (or Connection) is closed.

## <span class="header-section-number">5.3</span> CreateQueue

In the Qpid JMS client,
[Session\#createQueue()](&oracleJeeDocUrl;javax/jms/Session.html#createQueue(java.lang.String))
accepts either a queue name, or a Binding URL. If only name is specified
the destination will be resolved into binding URL:
direct://amq.direct//\<queue name\>?routingkey='\<queue
name\>'&durable='true'.

Calling Session\#createQueue() has no effect on the Broker.

Reiterating the advice from the JMS javadoc, it is suggested that this
method is not generally used. Instead, application should lookup
Destinations declared within JNDI.

## <span class="header-section-number">5.4</span> CreateTopic

In the Qpid JMS client,
[Session\#createTopic()](&oracleJeeDocUrl;javax/jms/Session.html#createTopic(java.lang.String))
accepts either a topic name, or a Binding URL. If only name is specified
the destination will be resolved into binding URL:
topic://amq.topic//\<topic name\>?routingkey='\<topic name\>'.

Calling Session\#createTopic() has no effect on the Broker.

Reiterating the advice from the JMS javadoc, it is suggested that this
method is not generally used. Instead, application should lookup
Destinations declared within JNDI.

# <span class="header-section-number">6</span> MessageProducer

A MessageProducer sends a message an *Exchange*. It is the Exchange
(within the Broker) that routes the message to zero or more queue(s).
Routing is performed according to rules expressed as *bindings* between
the exchange and queues and a *routing key* included with each message.

To understand how this mechanism is used to deliver messages to queues
and topics, see
[Exchanges](&qpidJavaBrokerBook;Java-Broker-Concepts-Exchanges.html)
within the Java Broker book.

It is important to understand that when synchronous publish is not
exlicitly enabled,
[MessageProducer\#send()](&oracleJeeDocUrl;javax/jms/MessageProducer.html#send(javax.jms.Message))
is *asynchronous* in nature. When \#send() returns to the application,
the application cannot be certain if the Broker has received the
message. The Qpid JMS client may not have yet started to send the
message, the message could residing in a TCP/IP buffer, or the messages
could be in some intermediate buffer within the Broker. If the
application requires certainty the message has been received by the
Broker, a [transactional
session](&oracleJeeDocUrl;javax/jms/Session.html#SESSION_TRANSACTED)
*must* be used, or synchronous publishing must be enabled using either
the [system property](#JMS-Client-0-8-System-Properties-SyncPublish) or
the [connection URL
option](#JMS-Client-0-8-Connection-URL-ConnectionOptions-SyncPublish).

Qpid JMS MessageProducers have a number of features above that required
by JMS. These are described in the sub-sections that follow.

## <span class="header-section-number">6.1</span> Mandatory Messages

With this feature, publishing a message with a routing key for which no
binding exists on the exchange will result in the message being returned
to the publisher's connection.

The Message is returned to the application in an asynchronous fashion
via the Connection's
[ExceptionListener](&oracleJeeDocUrl;javax/jms/ExceptionListener.html).
When a message is returned, it will be invoked with a JMSException whose
linked exception is an
[AMQNoRouteException](JMS-Client-0-8-Appendix-Exceptions-AMQNoRouteException).
The returned message is available to the application by calling
AMQNoRouteException\#getUndeliveredMessage(). The ExceptionListener will
be invoked exactly once for each returned message.

If synchronous publishing has been enabled, and a mandatory message is
returned, the
[MessageProducer\#send()](&oracleJeeDocUrl;javax/jms/MessageProducer.html#send(javax.jms.Message))
method will throw a JMSException.

The mandatory message feature is turned *on* by default for Queue
destinations and *off* for Topic destinations. This can be overridden
using system properties
[`qpid.default_mandatory`](#JMS-Client-0-8-System-Properties-DefaultMandatory)
and
[`qpid.default_mandatory_topic`](#JMS-Client-0-8-System-Properties-DefaultMandatoryTopic)
for Queues and Topics respectively.

> **Note**
>
> If this the mandatory flag is not set, the Broker will treat [the
> messages as
> unroutable](&qpidJavaBrokerBook;Java-Broker-Concepts-Exchanges.html#Java-Broker-Concepts-Exchanges-UnroutableMessage).

## <span class="header-section-number">6.2</span> Close When No Route

With this feature, if a mandatory message is published with a routing
key for which no binding exists on the exchange the Broker will close
the connection. This client feature requires support for the
corresponding feature by the Broker.

To enable or disable from the client, use the Connection URL option
[`closeWhenNoRoute`](#JMS-Client-0-8-Connection-URL-ConnectionOptions-CloseWhenNoRoute).

See [Closing client connections on unroutable mandatory
messages](&qpidJavaBrokerBook;Java-Broker-Close-Connection-When-No-Route.html)
within the Java Broker book for full details of the functioning of this
feature.

## <span class="header-section-number">6.3</span> Immediate Messages

This feature is defined in [AMQP specifications](&amqpSrc;).

When this feature is enabled, when publishing a message the Broker
ensures that a Consumer is attached to queue. If there is no Consumer
attached to the queue, the message is returned to the publisher's
connection. The Message is returned to the application in an
asynchronous fashion using the Connection's
[ExceptionListener](&oracleJeeDocUrl;javax/jms/ExceptionListener.html).

The ExceptionListener will be invoked with a JMSException whose linked
exception is an
[AMQNoConsumersException](JMS-Client-0-8-Appendix-Exceptions-AMQNoConsumersException).
The returned message is available to the application by calling
AMQNoConsumersException\#getUndeliveredMessage(). The ExceptionListener
will be invoked exactly once for each returned message.

If synchronous publishing has been enabled, and an immediate message is
returned, the
[MessageProducer\#send()](&oracleJeeDocUrl;javax/jms/MessageProducer.html#send(javax.jms.Message))
method will throw a JMSException.

The immediate message feature is turned *off* by default. It can be
enabled with system property
[`qpid.default_immediate`](#JMS-Client-0-8-System-Properties-DefaultImmediate).

## <span class="header-section-number">6.4</span> Flow Control

With this feature, if a message is sent to a queue that is overflow, the
producer's session is blocked until the queue becomes underfull, or a
timeout expires. This client feature requires support for the
corresponding feature by the Broker.

To control the timeout use System property
[`qpid.flow_control_wait_failure`](#JMS-Client-0-8-System-Properties-FlowControlWaitFailure).
To control the frequency with which warnings are logged whilst a Session
is blocked, use System property
[`qpid.flow_control_wait_notify_period`](#JMS-Client-0-8-System-Properties-FlowControlWaitNotifyPeriod)

See [Producer Flow
Control](&qpidJavaBrokerBook;Java-Broker-Runtime-Disk-Space-Management.html#Qpid-Producer-Flow-Control)
within the Java Broker book for full details of the functioning of this
feature.

# <span class="header-section-number">7</span> MessageConsumer

A MessageConsumer receives messages from a Queue or Topic.

MessageConsumer objects are created from the Session.

Qpid JMS MessageConsumers have a number of features above that required
by JMS. These are described in the sub-sections that follow.

## <span class="header-section-number">7.1</span> Consumers have Exchange/Queue Declaration and Binding Side Effect

By default, calling
[Session\#createConsumer()](&oracleJeeDocUrl;javax/jms/Session.html#createConsumer(javax.jms.Destination))
will cause:

1.  If the exchange does not exist on the Broker, it will be created.
    The exchange is specified by the Binding URL associated with the
    Destination.

2.  If the queue does not exist on the Broker, it will be created. The
    queue is specified by the Binding URL associated with the
    Destination.

3.  If there is no binding between the exchange and queue, a binding
    will be created using the routingkey as a bindingkey. The exchange,
    queue and routing key are specified by the Binding URL associated
    with the Destination.

The exchange declare, queue declare and bind side effects can be
suppressed using system properties
[`qpid.declare_exchanges`](#JMS-Client-0-8-System-Properties-DeclareExchanges),
[`qpid.declare_queues`](#JMS-Client-0-8-System-Properties-DeclareQueues)
and [`qpid.bind_queues`](#JMS-Client-0-8-System-Properties-BindQueues).

## <span class="header-section-number">7.2</span> Topic Subscriptions

The Qpid JMS client implements each subscription to a Topic as separate
queue on the Broker. From the perspective of the JMS application this
implementational detail is irrelevant: the application never needs to
directly address these queues. However, these details are important when
considering Management and Operational concerns.

Durable topic subscriptions use a *durable* and *exclusive* queue named
as follows:

            clientid: + subscriptionId
          

where `subscriptionId` is that passed to the
[Session\#createDurableSubscriber(javax.jms.Topic,java.lang.String)](&oracleJeeDocUrl;javax/jms/Session.html#createDurableSubscriber(javax.jms.Topic,%20java.lang.String))

Calling
[Session\#unsubscribe(java.lang.String)](&oracleJeeDocUrl;javax/jms/Session.html#unsubscribe(java.lang.String))
deletes the underlying queue.

Non-durable topic subscriptions use a *non-durable*, *exclusive* and
*auto-delete* queue named as follows:

            tmp + _ + ip + _ + port + _ + sequence
          

where `ip` is the ip address of the client with dots replaced by
underscores, `port` is the ephemeral port number assigned to the
client's connection, and `sequence` is a sequence number.

Closing the consumer (or closing the connection) will delete the
underlying queue.

## <span class="header-section-number">7.3</span> Maximum Delivery Count

With this feature, the Broker keeps track of a number of times a message
has been delivered to a consumer. If the count ever exceeds a threshold
value, the Broker moves the message to a dead letter queue (DLQ). This
is used to prevent poison messages preventing a system's operation. This
client feature requires support for the corresponding feature by the
Broker.

When using this feature, the application must either set system property
[qpid.reject.behaviour](#JMS-Client-0-8-System-Properties-RejectBehaviour)
or the Binding URL option
[`rejectbehaviour`](#JMS-Client-0-8-Binding-URL-Options-RejectBehaviour)
to the value `server`.

See [Handling Undeliverable
Messages](&qpidJavaBrokerBook;Java-Broker-Runtime-Handling-Undeliverable-Messages.html#Java-Broker-Runtime-Handling-Undeliverable-Messages-Maximum-Delivery-Count)
within the Java Broker book for full details of the functioning of this
feature.

> **Note**
>
> The optional JMS message header `JMSXDeliveryCount` is *not*
> supported.

# <span class="header-section-number">8</span> Destinations

A Destination is either a Queue or Topic. In the Qpid JMS client a
Destination encapsulates a Binding URL. In simple terms, the Binding URL
comprises of an exchange, queue and a routing key. Binding URLs are
described fully by ?.

In many cases, applications do not need to deal directly with Binding
URLs, instead they can refer to JMS administered objects declared in the
JNDI properties file with the `queue.` and `topic.` prefix to create
Queues and Topics objects respectively.

------------------------------------------------------------------------

1.  <div id="fn1">

    </div>

    Constructors of the AMQConnection class must not be
    used.[↩](#fnref1)


