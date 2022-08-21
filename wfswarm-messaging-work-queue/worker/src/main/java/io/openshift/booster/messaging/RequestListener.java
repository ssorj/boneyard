/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package io.openshift.booster.messaging;

import java.util.concurrent.atomic.AtomicInteger;
import javax.ejb.ActivationConfigProperty;
import javax.ejb.MessageDriven;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.inject.Inject;
import javax.jms.Destination;
import javax.jms.JMSConnectionFactory;
import javax.jms.JMSContext;
import javax.jms.JMSException;
import javax.jms.JMSProducer;
import javax.jms.Message;
import javax.jms.MessageListener;
import javax.jms.MessageProducer;
import javax.jms.Session;
import javax.jms.TextMessage;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import org.jboss.logging.Logger;

@MessageDriven(activationConfig = {
        @ActivationConfigProperty(propertyName = "connectionFactory", propertyValue = "factory1"),
        @ActivationConfigProperty(propertyName = "user", propertyValue = "work-queue"),
        @ActivationConfigProperty(propertyName = "password", propertyValue = "work-queue"),
        @ActivationConfigProperty(propertyName = "destination", propertyValue = "queue1"),
        @ActivationConfigProperty(propertyName = "jndiParameters", propertyValue = "java.naming.factory.initial=org.apache.qpid.jms.jndi.JmsInitialContextFactory;connectionFactory.factory1=amqp://${env.MESSAGING_SERVICE_HOST:localhost}:${env.MESSAGING_SERVICE_PORT:5672};queue.queue1=work-queue/requests"),
    })
@TransactionAttribute(TransactionAttributeType.NOT_SUPPORTED)
public class RequestListener implements MessageListener {
    private static final Logger log = Logger.getLogger(RequestListener.class);

    @Inject
    private Worker worker;

    @Inject
    @JMSConnectionFactory("java:global/jms/default")
    private JMSContext jmsContext;

    @Override
    public void onMessage(Message message) {
        log.infof("%s: Processing request %s", worker.id, message);

        TextMessage request = (TextMessage) message;
        String responseText;

        try {
            responseText = processRequest(request);
        } catch (Exception e) {
            log.errorf("%s: Failed processing: %s", worker.id, e.getMessage());
            return;
        }

        JMSProducer producer = jmsContext.createProducer();
        TextMessage response = jmsContext.createTextMessage();
        Destination responses;

        try {
            response.setJMSCorrelationID(request.getJMSMessageID());
            response.setStringProperty("workerId", worker.id);
            response.setText(responseText);

            responses = request.getJMSReplyTo();
        } catch (JMSException e) {
            worker.processingErrors.incrementAndGet();
            throw new RuntimeException(e);
        }

        producer.send(responses, response);

        worker.requestsProcessed.incrementAndGet();

        log.infof("%s: Sent %s", worker.id, response);
    }

    private String processRequest(TextMessage request) throws Exception {
        boolean uppercase = request.getBooleanProperty("uppercase");
        boolean reverse = request.getBooleanProperty("reverse");
        String text = request.getText();

        if (uppercase) {
            text = text.toUpperCase();
        }

        if (reverse) {
            text = new StringBuilder(text).reverse().toString();
        }

        return text;
    }
}
