package net.example;

import java.io.ByteArrayOutputStream; // XXX
import java.io.InputStream;
import java.io.IOException; // XXX
import java.net.URI;
import java.util.Hashtable;
import java.util.UUID;
import java.util.concurrent.SynchronousQueue;
import javax.inject.Singleton;
import javax.jms.CompletionListener;
import javax.jms.ConnectionFactory;
import javax.jms.JMSConsumer;
import javax.jms.JMSContext;
import javax.jms.JMSException;
import javax.jms.JMSProducer;
import javax.jms.Message;
import javax.jms.Queue;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.ws.rs.Consumes;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Response;
import org.glassfish.jersey.netty.httpserver.NettyHttpContainerProvider;
import org.glassfish.jersey.server.ResourceConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Singleton
@Path("/")
public class Frontend {
    private static Logger log = LoggerFactory.getLogger(Frontend.class);
    private static ConnectionFactory connectionFactory = null;

    public static void main(String[] args) {
        try {
            // AMQP

            String amqpHost = System.getenv("MESSAGING_SERVICE_HOST");
            String amqpPort = System.getenv("MESSAGING_SERVICE_PORT");
            String user = System.getenv("MESSAGING_SERVICE_USER");
            String password = System.getenv("MESSAGING_SERVICE_PASSWORD");

            if (amqpHost == null) amqpHost = "localhost";
            if (amqpPort == null) amqpPort = "5672";
            if (user == null) user = "example";
            if (password == null) password = "example";

            String url = String.format("failover:(amqp://%s:%s)", amqpHost, amqpPort);

            Hashtable<Object, Object> env = new Hashtable<Object, Object>();
            env.put("connectionfactory.factory1", url);

            InitialContext context = new InitialContext(env);
            ConnectionFactory factory = (ConnectionFactory) context.lookup("factory1");

            Frontend.connectionFactory = factory;

            // HTTP

            String httpHost = System.getenv("HTTP_HOST");
            String httpPort = System.getenv("HTTP_PORT");

            if (httpHost == null) httpHost = "0.0.0.0";
            if (httpPort == null) httpPort = "8080";

            URI uri = URI.create(String.format("http://%s:%s/", httpHost, httpPort));
            ResourceConfig rc = new ResourceConfig(Frontend.class);

            NettyHttpContainerProvider.createHttp2Server(uri, rc, null);
        } catch (Exception e) {
            log.error("Startup failed", e);
            System.exit(1);
        }
    }

    private JMSContext jmsContext = Frontend.connectionFactory.createContext();

    @POST
    @Path("/api/send-request")
    @Consumes("text/plain")
    @Produces("text/plain")
    public String sendRequest(String word) throws InterruptedException {
        SynchronousQueue<String> result = new SynchronousQueue<>();

        synchronized (jmsContext) {
            Queue requestQueue = jmsContext.createQueue("example/requested-words");
            Queue responseQueue = jmsContext.createTemporaryQueue();
            JMSProducer producer = jmsContext.createProducer();
            JMSConsumer consumer = jmsContext.createConsumer(responseQueue);

            consumer.setMessageListener((response) -> {
                    String status;

                    try {
                        status = response.getBody(String.class);
                    } catch (JMSException e) {
                        log.error("Message access error", e);
                        return;
                    }

                    try {
                        result.put(status);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    }

                    log.info("FRONTEND: Received response '{}'", status);
                });

            producer.setAsync(new LoggingCompletionListener());
            producer.setJMSReplyTo(responseQueue);
            producer.setJMSCorrelationID(UUID.randomUUID().toString());
            producer.send(requestQueue, word);
        }

        log.info("FRONTEND: Sent request '{}'", word);

        return result.take() + "\n";
    }

    @GET
    @Path("/api/ready")
    @Produces("text/plain")
    public String ready() {
        log.info("FRONTEND: I am ready!");

        return "OK\n";
    }

    @GET
    @Path("/index.html")
    @Produces("text/html")
    public Response html() {
        InputStream in = getClass().getResourceAsStream("/index.html");
        return Response.ok(in, "text/html").build();
    }

    @GET
    @Path("/main.css")
    @Produces("text/css")
    public Response css() {
        InputStream in = getClass().getResourceAsStream("/main.css");
        return Response.ok(in, "text/css").build();
    }

    @GET
    @Path("/main.js")
    @Produces("application/javascript")
    public Response mainjs() {
        InputStream in = getClass().getResourceAsStream("/main.js");
        return Response.ok(in, "application/javascript").build();
    }

    // XXX Ugly workaround
    
    @GET
    @Path("/rhea.js")
    @Produces("application/javascript")
    public Response rheajs() throws IOException {
        InputStream in = getClass().getResourceAsStream("/rhea.js");
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();

        int read;
        byte[] data = new byte[16384];

        while ((read = in.read(data, 0, data.length)) != -1) {
            buffer.write(data, 0, read);
        }

        return Response.ok(buffer.toByteArray(), "application/javascript").build();
    }

    class LoggingCompletionListener implements CompletionListener {
        @Override
        public void onCompletion(Message message) {
            try {
                log.debug("FRONTEND: Receiver acknowledged '{}'", message.getBody(String.class));
            } catch (JMSException e) {
                log.error("Message access error", e);
            }
        }

        @Override
        public void onException(Message message, Exception e) {
            log.error("Send failed", e);
        }
    }
}
