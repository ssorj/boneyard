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
import java.util.UUID;
import javax.ejb.Schedule;
import javax.ejb.Singleton;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.inject.Inject;
import javax.jms.JMSConnectionFactory;
import javax.jms.JMSContext;
import javax.jms.JMSException;
import javax.jms.JMSProducer;
import javax.jms.Message;
import javax.jms.Topic;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import org.jboss.logging.Logger;

@Singleton
@TransactionAttribute(TransactionAttributeType.NOT_SUPPORTED)
public class Worker {
    private static final Logger log = Logger.getLogger(Worker.class);
    static final String id = "worker-wfswarm-" + UUID.randomUUID()
        .toString().substring(0, 4);

    static AtomicInteger requestsProcessed = new AtomicInteger(0);
    static AtomicInteger processingErrors = new AtomicInteger(0);

    @Inject
    @JMSConnectionFactory("java:global/jms/default")
    private JMSContext jmsContext;

    @Schedule(second = "*/5", minute = "*", hour = "*", persistent = false)
    public void sendUpdate() {
        log.debugf("%s: Sending status update", id);

        Topic workerStatus = jmsContext.createTopic("work-queue/worker-updates");
        JMSProducer producer = jmsContext.createProducer();
        Message message = jmsContext.createMessage();

        try {
            message.setStringProperty("workerId", id);
            message.setLongProperty("timestamp", System.currentTimeMillis());
            message.setLongProperty("requestsProcessed", requestsProcessed.get());
            message.setLongProperty("processingErrors", processingErrors.get());
        } catch (JMSException e) {
            throw new RuntimeException(e);
        }

        producer.send(workerStatus, message);
    }
}
