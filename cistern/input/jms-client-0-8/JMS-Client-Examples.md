# <span class="header-section-number">1</span> Examples

The following programs shows how to send and receive messages using the
Qpid JMS client. The first program illustrates a *point to point*
example, the second, a pubish/subscribe example.

Both examples show the use JNDI to obtain connection factory and
destination objects which the application needs. In this way the
configuration is kept separate from the application code itself.

The example code will be straightforward for anyone familiar with Java
JMS. Readers in need of an introduction are directed towards [Oracle's
JMS tutorial](&oracleJmsTutorial;).

# <span class="header-section-number">2</span> Point to point example

In this example, we illustrate point to point messaging. We create a
JNDI context using a properties file, use the context to lookup a
connection factory, create and start a connection, create a session, and
lookup a destination (a queue) from the JNDI context. Then we create a
producer and a consumer, send a message with the producer and receive it
with the consumer.

``` {.sourceCode .java}
import javax.jms.*;
import javax.naming.Context;
import javax.naming.InitialContext;
import java.util.Properties;

public class Hello {

    public Hello() {
    }

    public static void main(String[] args) throws Exception {
        Hello hello = new Hello();
        hello.runTest();
    }

    private void runTest() throws Exception {
      Properties properties = new Properties();
      properties.load(this.getClass().getResourceAsStream("helloworld.properties"));  
      Context context = new InitialContext(properties);                               

      ConnectionFactory connectionFactory
          = (ConnectionFactory) context.lookup("qpidConnectionFactory");              
      Connection connection = connectionFactory.createConnection();                   
      connection.start();                                                             

      Session session = connection.createSession(true, Session.SESSION_TRANSACTED);   
      Queue queue = (Queue) context.lookup("myqueue");                                

      MessageConsumer messageConsumer = session.createConsumer(queue);                
      MessageProducer messageProducer = session.createProducer(queue);                

      TextMessage message = session.createTextMessage("Hello world!");                
      messageProducer.send(message);
      session.commit();

      message = (TextMessage)messageConsumer.receive();                               
      session.commit();
      System.out.println(message.getText());

      connection.close();                                                             
      context.close();                                                                
    }
}
    
```

-   Loads the JNDI properties file, which specifies the connection
    factory, queues and topics. See ? for details.

-   Creates the JNDI initial context.

-   Looks up a JMS connection factory for Qpid.

-   Creates a JMS connection. Creating the JMS connections establishes
    the connection to the Broker.

-   Starts the connection, required for the consumption of messages.

-   Creates a transactional session.

-   Looks up a destination for the queue with JNDI name *myqueue*.

-   Creates a consumer that reads messages from the queue<span
    id="fnref1">[^1^](#fn1)</span>.

-   Creates a producer that sends messages to the queue.

-   Creates a new message of type *javax.jms.TextMessage*, publishes the
    message and commits the session.

-   Reads the next available message (awaiting indefinitely if
    necessary) and commits the session.

-   Closes the Connection. All sessions owned by the Connection along
    with their MessageConsumers and MessageProducers are automatically
    closed. The connection to the Broker is closed as this point.

-   Closes the JNDI context.

The contents of the `helloworld.properties` file are shown below.

``` {.properties}
java.naming.factory.initial = org.apache.qpid.jndi.PropertiesFileInitialContextFactory
connectionfactory.qpidConnectionFactory = amqp://guest:guest@clientid/?brokerlist='tcp://localhost:5672' 
queue.myqueue = queue1                                                                                   
    
```

-   Defines a connection factory from which Connections can be created.
    The syntax of a ConnectionURL is given in ?.

-   Defines a queue for which MessageProducers and/or MessageConsumers
    send and receive messages. The format of these entries is described
    in ?.

# <span class="header-section-number">3</span> Publish/subscribe example

In this second example, we illustrate publish/subscribe messaging.
Again, we create a JNDI context using a properties file, use the context
to lookup a connection factory, create and start a connection, create a
session, and lookup a destination (a topic) from the JNDI context. Then
we create a producer and two durable subscribers , send a message with
the producer. Both subscribers receive the same message.

``` {.sourceCode .java}
import javax.jms.*;
import javax.naming.Context;
import javax.naming.InitialContext;

import java.util.Properties;

public class StocksExample {

    public StocksExample() {
    }

    public static void main(String[] args) throws Exception {
      StocksExample stocks = new StocksExample();
      stocks.runTest();
    }

    private void runTest() throws Exception {
      Properties properties = new Properties();
      properties.load(this.getClass().getResourceAsStream("stocks.properties"));
      Context context = new InitialContext(properties);

      ConnectionFactory connectionFactory
          = (ConnectionFactory) context.lookup("qpidConnectionFactory");
      Connection connection = connectionFactory.createConnection();
      connection.start();

      Session session = connection.createSession(true, Session.SESSION_TRANSACTED);
      Topic priceTopic = (Topic) context.lookup("myprices");                             

      MessageConsumer subscriber1 = session.createDurableSubscriber(priceTopic, "sub1"); 
      MessageConsumer subscriber2 = session.createDurableSubscriber(priceTopic, "sub2" /*, "price > 150", false*/ );
      MessageProducer messageProducer = session.createProducer(priceTopic);

      Message message = session.createMessage();
      message.setStringProperty("instrument", "IBM");
      message.setIntProperty("price", 100);
      messageProducer.send(message);
      session.commit();

      message = subscriber1.receive(1000);
      session.commit();
      System.out.println("Subscriber 1 received : " + message);

      message = subscriber2.receive(1000);
      session.commit();
      System.out.println("Subscriber 2 received : " + message);

      session.unsubscribe("sub1");                                                       
      session.unsubscribe("sub2");
      connection.close();
      context.close();
    }
}
    
```

-   Looks up a destination for the topic with JNDI name myprices.

-   Creates two durable subscribers, `sub1` and `sub2`. Durable
    subscriptions retain messages for the client even when the client is
    disconnected, until the subscription is unsubscribed. Subscription 2
    has a (commented out) message selector argument so you can
    conveniently experiement with the effect of those. <span
    id="fnref2">[^2^](#fn2)</span>

-   Unsubscribes the two durable subscribers, permanently removing the
    knowledge of the subscriptions from the system. An application would
    normally *NOT* do this. The typical use-case for durable subsciption
    is one where the subscription exists over an extended period of
    time.

The contents of the `stocks.properties` file are shown below.

    java.naming.factory.initial = org.apache.qpid.jndi.PropertiesFileInitialContextFactory
    connectionfactory.qpidConnectionFactory = amqp://guest:guest@clientid/?brokerlist='tcp://localhost:5672'
    topic.myprices = prices 
        

-   Defines a topic for which MessageProducers and/or MessageConsumers
    send and receive messages. The format of this entry is described in
    ?.

------------------------------------------------------------------------

1.  <div id="fn1">

    </div>

    Creating consumer will automatically create the queue on the Broker
    and bind it to an exchange. Specifically, in this case as the
    `queue.` form is used in the JNDI properties the effect will be to
    create a queue called `queue1` on the Broker, and create a binding
    between the `amq.direct` exchange and this queue using the queue's
    name. This process is described in detail in ?[↩](#fnref1)

2.  <div id="fn2">

    </div>

    Each durable subscription is implemented as a queue on the Broker.
    See ? for details.[↩](#fnref2)


