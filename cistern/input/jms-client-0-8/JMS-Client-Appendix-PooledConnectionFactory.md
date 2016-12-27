# <span class="header-section-number">1</span> PooledConnectionFactory

Qpid client provides `PooledConnectionFactory` which is a special
implementation of
[ConnectionFactory](&oracleJeeDocUrl;javax/jms/ConnectionFactory.html)
supporting [Connection](&oracleJeeDocUrl;javax/jms/Connection.html)
pooling.

The `PooledConnectionFactory` caches a predefined number of connections
thus saving an application which connects frequently time. The
`Connection` instance is taken from the pool whenever method
`PooledConnectionFactory#createConnection()` is invoked and returned
into the pool when method `Connection#close()` is called.

A user can configure a maximum allowed number of connections to remain
in pool (10 by default) by calling
`PooledConnectionFactory#setMaxPoolSize(int)`. When number of
connections exceeds the value set for maximum pool size,
`PooledConnectionFactory` starts to work as a normal
[ConnectionFactory](&oracleJeeDocUrl;javax/jms/ConnectionFactory.html)
and creates a new connection every time method
`PooledConnectionFactory#createConnection()` is invoked.

The [Connection URL](#JMS-Client-0-8-Connection-URL) is set by invoking
method `PooledConnectionFactory#setConnectionURLString(String)`.

A user can specify the maximum time a connection may remain idle in pool
by calling `PooledConnectionFactory#setConnectionTimeout(long)` passing
a value in milliseconds. If connection is not used within the specified
interval it is closed automatically.

This implementation can be useful in *Spring JMS* based applications. An
example below demonstrates how to configure `PooledConnectionFactory` in
the Spring xml configuration.

``` {.sourceCode .xml}
<bean id="pooledConnectionFactory" class="org.apache.qpid.client.PooledConnectionFactory">
  <!-- set maximum number of pool connections to 20-->
  <property name="maxPoolSize" value="20"></property>
  <!-- set the timeout for connection to remain open in pool without being used -->
  <property name="connectionTimeout" value="60000"></property>
  <!-- set connection URL as String -->
  <property name="connectionURLString" value="amqp://guest:guest@clientid/default?brokerlist='tcp://localhost:5672?retries='300'&amp;failover='nofailover''&amp;maxprefetch='0'"></property>
</bean>
```

*PooledConnectionFactory* spring bean can be configured with such
*spring-jms* beans like *DefaultMessageListenerContainer* and
*JmsTemplate*. The example below demonstrates how to do that

``` {.sourceCode .xml}
<bean id="jmsProducerTemplate" class="org.springframework.jms.core.JmsTemplate">
    <!-- set reference to pooledConnectionFactory bean -->
    <property name="connectionFactory" ref="pooledConnectionFactory"></property>
    <property name="defaultDestination" ref="destination" />
</bean>

<bean id="jmsContainer" class="org.springframework.jms.listener.DefaultMessageListenerContainer">
    <!-- set reference to pooledConnectionFactory bean -->
    <property name="connectionFactory" ref="pooledConnectionFactory"/>
    <property name="destination" ref="destination"/>
    <property name="messageListener" ref="messageListener" />
</bean>
```

> **Note**
>
> If using `DefaultMessageListenerContainer` with `cacheLevel` set to
> `NONE` it is important that `maxConcurrentConsumer` does not exceed
> the value of maximum pool size set on `PooledConnectionFactory` bean.
> If this is not the case, once the number of in-use connections reaches
> the the *PooledConnectionFactory\#maxPoolSize* a new connection will
> be opened for each and every message receipt i.e. a connection per
> message anti-pattern.
