package net.example;

import java.net.URI;
import java.util.Hashtable;
import javax.inject.Singleton;
import javax.jms.ConnectionFactory;
import javax.jms.CompletionListener;
import javax.jms.Destination;
import javax.jms.JMSConsumer;
import javax.jms.JMSContext;
import javax.jms.JMSException;
import javax.jms.JMSProducer;
import javax.jms.Message;
import javax.jms.Queue;
import javax.jms.TextMessage;
import javax.jms.Topic;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.ws.rs.Consumes;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import org.glassfish.jersey.netty.httpserver.NettyHttpContainerProvider;
import org.glassfish.jersey.server.ResourceConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Singleton
@Path("/")
public class Processor {
    private static Logger log = LoggerFactory.getLogger(Processor.class);
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

            String url = String.format("failover:(amqp://%s:%s)?jms.prefetchPolicy.all=0", amqpHost, amqpPort);

            Hashtable<Object, Object> env = new Hashtable<Object, Object>();
            env.put("connectionfactory.factory1", url);

            InitialContext context = new InitialContext(env);
            ConnectionFactory factory = (ConnectionFactory) context.lookup("factory1");

            Processor.connectionFactory = factory;

            // HTTP

            String httpHost = System.getenv("HTTP_HOST");
            String httpPort = System.getenv("HTTP_PORT");

            if (httpHost == null) httpHost = "0.0.0.0";
            if (httpPort == null) httpPort = "8080";

            URI uri = URI.create(String.format("http://%s:%s/", httpHost, httpPort));
            ResourceConfig rc = new ResourceConfig(Processor.class);

            NettyHttpContainerProvider.createHttp2Server(uri, rc, null);
        } catch (Exception e) {
            log.error("Startup failed", e);
            System.exit(1);
        }
    }

    private JMSContext jmsContext = Processor.connectionFactory.createContext();

    public Processor() {
        synchronized (jmsContext) {
            Queue requestQueue = jmsContext.createQueue("example/requested-words");
            Topic publishTopic = jmsContext.createTopic("example/processed-words");
            JMSConsumer consumer = jmsContext.createConsumer(requestQueue);
            JMSProducer responseProducer = jmsContext.createProducer();
            JMSProducer publishProducer = jmsContext.createProducer();

            consumer.setMessageListener((request) -> {
                    String word;
                    Destination responseQueue;
                    String correlationId;

                    try {
                        word = request.getBody(String.class);
                        responseQueue = request.getJMSReplyTo();
                        correlationId = request.getJMSCorrelationID();
                    } catch (JMSException e) {
                        log.error("Message access error", e);
                        return;
                    }

                    log.info("PROCESSOR: Received request '{}'", word);

                    String result = checkWord(word);

                    if (result == "OK") {
                        publishProducer.setAsync(new LoggingCompletionListener());
                        publishProducer.send(publishTopic, word);

                        log.info("PROCESSOR: Published word '{}'", word);
                    }

                    responseProducer.setAsync(new LoggingCompletionListener());
                    responseProducer.setJMSCorrelationID(correlationId);
                    responseProducer.send(responseQueue, result);

                    log.info("PROCESSOR: Sent response '{}'", result);
                });
        }
    }

    private String checkWord(String word) {
        return "OK";
    }

    @GET
    @Path("/api/ready")
    @Produces("text/plain")
    public String ready() {
        log.info("PROCESSOR: I am ready!");

        return "OK\n";
    }

    class LoggingCompletionListener implements CompletionListener {
        @Override
        public void onCompletion(Message message) {
            try {
                log.debug("PROCESSOR: Receiver acknowledged '{}'", message.getBody(String.class));
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
