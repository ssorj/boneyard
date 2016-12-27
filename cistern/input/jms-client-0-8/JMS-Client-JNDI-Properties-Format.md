# <span class="header-section-number">1</span> JNDI Properties Format

The Qpid JMS Client comes with own JNDI context factory
`org.apache.qpid.jndi.PropertiesFileInitialContextFactory` which
utilises a Java properties file for declaring the JMS administered
objects: connection factories, queues, topics and destinations. It uses
the following syntax:

    connectionfactory.<jndi name>=<connection url>
    queue.<jndi name>=<queue name>
    topic.<jndi name>=<topic name>
    destination.<jndi name>=<binding url>

An arbitrary number of connection factories, queues, topics, queues or
destinations or can be declared in the JNDI properties file. Each JNDI
name must be unique.

The application looks up the objects via an InitialContext. This lookup
and an example JNDI properties file is provided in ?

We now consider each JMS administered object type in turn.

# <span class="header-section-number">2</span> ConnectionFactory

`connectionfactory.`*name* declares a
[ConnectionFactory](&oracleJeeDocUrl;javax/jms/ConnectionFactory.html)
with the given JNDI name. The value must be a legal Connection URL.

See ? for format of the URL and its permitted options.

# <span class="header-section-number">3</span> Queue

`queue.`*name* declares a [Queue](&oracleJeeDocUrl;javax/jms/Queue.html)
with the given JNDI name. The value is simple queue name. This is the
name of the queue as known by the Broker.

The `queue.` form is a short hand for declaring a destination:

    destination.name=direct://amq.direct//<queue name>?routingkey=’<queue name>’&durable=’true’

# <span class="header-section-number">4</span> Topic

`topic.`*name* declares a [Topic](&oracleJeeDocUrl;javax/jms/Topic.html)
with the given JNDI name. The value is topic name. This topic name is
used on the Broker as a binding key between the `amq.topic` exchange and
the queue corresponding to the topic subscriber.

The `topic.` form is a short hand for declaring a destination:

    destination.name=topic://amq.topic/<topic name>/?routingkey=<topic name>

# <span class="header-section-number">5</span> Destination

`destination.`*name* declares either a
[Queue](&oracleJeeDocUrl;javax/jms/Queue.html) or
[Topic](&oracleJeeDocUrl;javax/jms/Topic.html) (depending on the class)
with the given JNDI name. The value must be a Binding URL.

See ? for format of the URL and its permitted options.
