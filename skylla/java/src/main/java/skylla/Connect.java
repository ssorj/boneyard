package skylla;

import org.apache.qpid.jms.JmsConnectionFactory;

import javax.jms.*;
import javax.naming.Context;
import java.util.Hashtable;

public class Connect {
    public static void main(String[] args) throws Exception {
        String authority = args[0];
        
        Connection connection = null;
        ConnectionFactory connectionFactory = new JmsConnectionFactory("amqp://" + authority + "?amqp.saslMechanisms=GSSAPI");

        try {
            connection = connectionFactory.createConnection();
            System.out.println("Connected!");

            Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
            System.out.println("Created session " + session);

            TemporaryQueue queue = session.createTemporaryQueue();
            System.out.println("Created queue " + queue);

            // MessageProducer producer = session.createProducer(queue);
            // System.out.println("Created producer " + producer);

            // MessageConsumer consumer = session.createConsumer(queue);
            // System.out.println("Created consumer " + consumer);

            // TextMessage smessage = session.createTextMessage("abc");
            // System.out.println("Created message " + smessage);

            // producer.send(smessage);
            // System.out.println("Sent message " + smessage);

            // TextMessage rmessage = (TextMessage) consumer.receive();
            // System.out.println("Received message " + rmessage);
        } finally {
            if (connection != null) {
                connection.close();
            }
        }
    }
}
