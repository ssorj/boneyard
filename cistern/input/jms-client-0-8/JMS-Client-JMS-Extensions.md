# <span class="header-section-number">1</span> JMS Extensions

This section illustrates using Qpid specific extentions to JMX for the
managament of queues, exchanges and bindings.

> **Important**
>
> It is not recommended that these extensions are generally used. These
> interfaces are subject to change and will not be supported in this
> form for AMQP 1.0. Instead, the reader is directed towards the
> Managment interfaces of the Broker.

# <span class="header-section-number">2</span> Queue Management

These extensions allow queues to be created or removed.

## <span class="header-section-number">2.1</span> Queue creation

The following example illustrates the creation of the a LVQ queue from a
javax.jms.Session object. Note that this utilises a Qpid specific
extension to JMS and involves casting the session object back to its
Qpid base-class.

    Map<String,Object> arguments = new HashMap<String, Object>();
    arguments.put("qpid.last_value_queue_key","ISIN");
    AMQDestination amqQueue = (AMQDestination) context.lookup("myqueue");
    ((AMQSession<?,?>) session).createQueue(
            AMQShortString.valueOf(amqQueue.getQueueName()),
            amqQueue.isAutoDelete(),
            amqQueue.isDurable(),
            amqQueue.isExclusive(),
            arguments);

# <span class="header-section-number">3</span> Binding Management

These extensions allow bindings to be created or removed.

## <span class="header-section-number">3.1</span> Binding creation

The following example illustrates the creation of queue binding to topic
exchange with JMS client.

    ConnectionFactory connectionFactory = ...
    Connection connection = connectionFactory.createConnection();
    AMQSession<?, ?> session = (AMQSession<?,?>)connection.createSession(false, Session.AUTO_ACKNOWLEDGE);

    ...

    AMQShortString queueName = new AMQShortString("testQueue");
    AMQShortString routingKey = new AMQShortString("testRoutingKey");
    AMQDestination destination = (AMQDestination) session.createQueue(queueName.asString());

    ...

    // binding arguments
    Map<String, Object> arguments = new HashMap<String, Object>();
    arguments.put("x-filter-jms-selector", "application='app1'");

    // create binding
    session.bindQueue(queueName, routingKey, FieldTable.convertToFieldTable(arguments),
        new AMQShortString("amq.topic"), destination);
