# <span class="header-section-number">1</span> Closing client connections on unroutable mandatory messages

## <span class="header-section-number">1.1</span> Summary

Due to asynchronous nature of AMQP 0-8/0-9/0-9-1 protocols sending a
message with a routing key for which no queue binding exist results in
either message being bounced back (if it is mandatory or immediate) or
discarded on broker side otherwise.

When a 'mandatory' message is returned back, the Qpid JMS client conveys
this by delivering an *AMQNoRouteException* through the configured
ExceptionListener on the Connection. This does not cause channel or
connection closure, however it requires a special exception handling on
client side in order to deal with *AMQNoRouteExceptions*. This could
potentially be a problem when using various messaging frameworks (e.g.
Mule) as they usually close the connection on receiving any
JMSException.

In order to simplify application handling of scenarios where 'mandatory'
messages are being sent to queues which do not actually exist, the Java
Broker can be configured such that it will respond to this situation by
closing the connection rather than returning the unroutable message to
the client as it normally should. From the application perspective, this
will result in failure of synchronous operations in progress such as a
session commit() call.

> **Note**
>
> This feature affects only transacted sessions.
>
> Qpid JMS client sends 'mandatory' messages when using Queue
> destinations and 'non-mandatory' messages when using Topic
> destinations.

## <span class="header-section-number">1.2</span> Configuring *closeWhenNoRoute*

The Broker attribute *closeWhenNoRoute* can be set to specify this
feature on broker side. By default, it is turned on. Setting
*closeWhenNoRoute* to *false* switches it off.

Setting the *closeWhenNoRoute* in the JMS client connection URL can
override the broker configuration on a connection specific basis, for
example :

    amqp://guest:guest@clientid/?brokerlist='tcp://localhost:5672'&closeWhenNoRoute='false'

If no value is specified on the client the broker setting will be used.
If client setting is specified then it will take precedence over the
broker-wide configuration. If the client specifies and broker does not
support this feature the warning will be logged.
