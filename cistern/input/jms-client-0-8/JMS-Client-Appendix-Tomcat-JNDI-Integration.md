# <span class="header-section-number">1</span> How to bind Qpid destinations and connection factories into Tomcat JNDI

Qpid client destinations and connection factories can be registered in
external JNDI containers, for example, Tomcat JNDI implementation.

`org.apache.qpid.jndi.ObjectFactory` implements
[javax.naming.spi.ObjectFactory](&oracleJdkDocUrl;javax/naming/spi/ObjectFactory.html)
allowing it to create instances of `AMQConnectionFactory`,
`PooledConnectionFactory`, `AMQConnection`, `AMQQueue` and `AMQTopic` in
external JNDI container from
[javax.naming.Reference](&oracleJdkDocUrl;javax/naming/Reference.html)s.

Additionally, `AMQConnectionFactory`, `PooledConnectionFactory` and
`AMQDestination` (parent of `AMQQueue` and `AMQTopic`) implement
[javax.naming.Referenceable](&oracleJdkDocUrl;javax/naming/Referenceable.html)
allowing creation of
[javax.naming.Reference](&oracleJdkDocUrl;javax/naming/Reference.html)
objects for binding in external JNDI implementations.

`org.apache.qpid.jndi.ObjectFactory` allows the creation of:

-   an instance of `ConnectionFactory` from a `Reference` containing
    reference address
    ([javax.naming.RefAddr](&oracleJdkDocUrl;javax/naming/RefAddr.html))
    `connectionURL` with content set to a [Connection
    URL](#JMS-Client-0-8-Connection-URL).

-   an instance of `PooledConnectionFactory` from a `Reference`
    containing reference address
    ([javax.naming.RefAddr](&oracleJdkDocUrl;javax/naming/RefAddr.html))
    `connectionURL` with content set to a [Connection
    URL](#JMS-Client-0-8-Connection-URL).

-   an instance of `AMQConnection` from a `Reference` containing
    reference address
    ([javax.naming.RefAddr](&oracleJdkDocUrl;javax/naming/RefAddr.html))
    `connectionURL` with content set to a [Connection
    URL](#JMS-Client-0-8-Connection-URL).

-   an instance of `AMQQueue` from a `Reference` containing reference
    address
    ([javax.naming.RefAddr](&oracleJdkDocUrl;javax/naming/RefAddr.html))
    `address` with content set to either
    [Address](&qpidProgrammingBook;) or [Binding
    URL](#JMS-Client-0-8-Binding-URL).

-   an instance of `AMQTopic` from a `Reference` containing reference
    address
    ([javax.naming.RefAddr](&oracleJdkDocUrl;javax/naming/RefAddr.html))
    `address` with content set to either
    [Address](&qpidProgrammingBook;) or [Binding
    URL](#JMS-Client-0-8-Binding-URL).

> **Note**
>
> For `AMQQueue` and `AMQTopic` prefix `BURL:` need to be specified for
> [Binding URL](#JMS-Client-0-8-Binding-URL). Otherwise, client will try
> to parse content using [Address](&qpidProgrammingBook;) format.

An example below demonstrates how to create JNDI resources in the Tomcat
container using Resource declarations in context.xml (A Tomcat specific
web application configuration file usually added into war under
/META-INF/context.xml).

``` {.sourceCode .xml}
<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE xml>
<Context>

  <Resource name="jms/connectionFactory" auth="Container"
            type="org.apache.qpid.client.AMQConnectionFactory"
            factory="org.apache.qpid.jndi.ObjectFactory"
            connectionURL="amqp://guest:guest@clientid/?brokerlist='localhost:5672'"/>

  <Resource name="jms/pooledConnectionFactory" auth="Container"
            type="org.apache.qpid.client.PooledConnectionFactory"
            factory="org.apache.qpid.jndi.ObjectFactory"
            connectionURL="amqp://guest:guest@clientid/?brokerlist='localhost:5672'"
            maxPoolSize="20" connectionTimeout="60000"/>

  <Resource name="jms/queue" auth="Container"
            type="org.apache.qpid.client.AMQQueue"
            factory="org.apache.qpid.jndi.ObjectFactory"
            address="BURL:direct://amq.direct//myQueue?durable='true'"/>

  <Resource name="jms/topic" auth="Container"
            type="org.apache.qpid.client.AMQTopic"
            factory="org.apache.qpid.client.AMQConnectionFactory"
            address="BURL:topic://amq.topic//myTopic?routingkey='myTopic'"/>

</Context>
```

In the example above `AMQConnectionFactory` would be registered under
JNDI name "jms/connectionFactory", `PooledConnectionFactory` would be
registered under JNDI name "jms/pooledConnectionFactory", `Queue`
"myQueue" would be registered under JNDI name "jms/queue" and JMS
`Topic` destination "myTopic" would be registered under JNDI name
"jms/topic". (All resources will be bound under "java:comp/env"). On
declaration of `PooledConnectionFactory` optional maxPoolSize and
connectionTimeout are set to 20 and 60000 milliseconds accordingly.

The client application can find the resources declared in Tomcat
context.xml using the code below:

``` {.sourceCode .java}
    Context context = new InitialContext();
    Context environmentContext = (Context)context.lookup("java:comp/env");
    ...
    ConnectionFactory connectionFactory = (ConnectionFactory) environmentContext.lookup("jms/connectionFactory");
    ...
    Queue queue = (Queue)environmentContext.lookup("jms/queue");
    ...
    Topic topic = (Topic)environmentContext.lookup("jms/topic");
    ...
```

> **Note**
>
> In order to support backward compatibility `AMQConnectionFactory`
> continues to implement
> [javax.naming.spi.ObjectFactory](&oracleJdkDocUrl;javax/naming/spi/ObjectFactory.html)
> and can be used to instantiate JNDI resources from
> [javax.naming.Reference](&oracleJdkDocUrl;javax/naming/Reference.html)s.
> However, its method `getObjectInstance` is marked as `Deprecated` and
> will be removed in future version of client. For backward
> compatibility, Qpid JNDI resources can be declared using fully
> qualified class names as addresses. That will became unsupported in
> future version as well. An example of Tomcat context.xml with
> declarations of JNDI resources using deprecated factory and addresses
> is provided below.
>
> ``` {.sourceCode .xml}
> <?xml version='1.0' encoding='utf-8'?>
> <!DOCTYPE xml>
> <Context>
>
>   <Resource name="jms/queue" auth="Container"
>             type="org.apache.qpid.client.AMQQueue"
>             factory="org.apache.qpid.client.AMQConnectionFactory"
>             org.apache.qpid.client.AMQQueue="direct://amq.direct//myDurableQueue?durable='true'"/>
>
>   <Resource name="jms/topic" auth="Container"
>             type="org.apache.qpid.client.AMQTopic"
>             factory="org.apache.qpid.client.AMQConnectionFactory"
>             org.apache.qpid.client.AMQTopic="topic://amq.topic//myTopic?routingkey='myTopic'"/>
>
>   <Resource name="jms/connectionFactory" auth="Container"
>             type="org.apache.qpid.client.AMQConnectionFactory"
>             factory="org.apache.qpid.client.AMQConnectionFactory"
>             org.apache.qpid.client.AMQConnectionFactory="amqp://guest:guest@clientid/?brokerlist='localhost:5672'"/>
>
> </Context>
> ```
