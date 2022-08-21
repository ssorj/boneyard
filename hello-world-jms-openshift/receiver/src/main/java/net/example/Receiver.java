package net.example;

import io.netty.channel.Channel;
import java.net.URI;
import java.util.Hashtable;
import javax.inject.Singleton;
import javax.jms.Connection;
import javax.jms.ConnectionFactory;
import javax.jms.JMSException;
import javax.jms.MessageConsumer;
import javax.jms.Queue;
import javax.jms.Session;
import javax.jms.TextMessage;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.ws.rs.GET;
import javax.ws.rs.InternalServerErrorException;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import org.glassfish.jersey.netty.httpserver.NettyHttpContainerProvider;
import org.glassfish.jersey.server.ResourceConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Singleton
@Path("/api")
public class Receiver {
    private static Logger log = LoggerFactory.getLogger(Receiver.class);
    
    public static void main(String[] args) {
        try {
            String host = System.getenv("HTTP_HOST");
            String port = System.getenv("HTTP_PORT");

            if (host == null) host = "0.0.0.0";
            if (port == null) port = "8080";

            URI uri = URI.create(String.format("http://%s:%s/", host, port));
            ResourceConfig rc = new ResourceConfig(Receiver.class);

            NettyHttpContainerProvider.createHttp2Server(uri, rc, null);
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    MessageConsumer consumer;

    public Receiver() throws NamingException, JMSException {
        String host = System.getenv("MESSAGING_SERVICE_HOST");
        String port = System.getenv("MESSAGING_SERVICE_PORT");
        String user = System.getenv("MESSAGING_SERVICE_USER");
        String password = System.getenv("MESSAGING_SERVICE_PASSWORD");

        if (host == null) host = "localhost";
        if (port == null) port = "5672";
        if (user == null) user = "example";
        if (password == null) password = "example";

        String url = String.format("failover:(amqp://%s:%s)", host, port);
        String address = "example/strings";

        Hashtable<Object, Object> env = new Hashtable<Object, Object>();
        env.put("connectionfactory.factory1", url);

        InitialContext context = new InitialContext(env);
        ConnectionFactory factory = (ConnectionFactory) context.lookup("factory1");
        Connection conn = factory.createConnection(user, password);

        log.info("RECEIVER: Connecting to '{}'", url);

        conn.start();

        synchronized (this) {
            Session session = conn.createSession(false, Session.AUTO_ACKNOWLEDGE);
            Queue queue = session.createQueue(address);
            consumer = session.createConsumer(queue);
        }
    }

    @POST
    @Path("/receive")
    @Produces(MediaType.TEXT_PLAIN)
    public String receive() {
        TextMessage message;
        String text;

        try {
            synchronized (this) {
                message = (TextMessage) consumer.receiveNoWait();

                if (message == null) {
                    return null;
                }

                text = message.getText();
            }
        } catch (JMSException e) {
            e.printStackTrace();
            throw new InternalServerErrorException(e);
        }

        log.info("RECEIVER: Received message '{}'", text);

        return text;
    }

    @GET
    @Path("/health")
    @Produces(MediaType.TEXT_PLAIN)
    public String health() {
        return "OK\n";
    }
}
