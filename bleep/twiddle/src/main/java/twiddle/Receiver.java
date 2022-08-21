/*
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
 */

package twiddle;

import java.util.Arrays;
import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;
import javax.jms.BytesMessage;
import javax.jms.Connection;
import javax.jms.Destination;
import javax.jms.Message;
import javax.jms.MessageConsumer;
import javax.jms.MessageProducer;
import javax.jms.Session;

public class Receiver implements Runnable {
    String id;
    Connection conn;
    Destination dest;
    Random rng = new Random();

    public Receiver(String id, Connection conn, Destination dest) {
        this.id = id;
        this.conn = conn;
        this.dest = dest;
    }

    public void run() {
        try {
            boolean transacted = rng.nextBoolean();
            int acknowledgeMode = Main.getAcknowledgeMode();

            Session session = conn.createSession(transacted, acknowledgeMode);
            MessageProducer producer = session.createProducer(dest);
            MessageConsumer consumer = session.createConsumer(dest);

            while (true) {
                Thread.sleep(rng.nextInt(100));

                BytesMessage message = (BytesMessage) consumer.receive();

                if (session.getAcknowledgeMode() == Session.CLIENT_ACKNOWLEDGE) {
                    message.acknowledge();
                }

                if (rng.nextInt(10) == 0) {
                    producer.send(session.createBytesMessage());
                }

                if (rng.nextInt(10) == 0) {
                    if (session.getTransacted()) {
                        if (rng.nextBoolean()) {
                            session.commit();
                        } else {
                            session.rollback();
                        }
                    } else {
                        session.recover();
                    }
                }

                String log = String.format("%s: body-length=%d, delivery-mode=%d, priority=%d, expiration=%d, " +
                                           "transacted=%b, acknowledge-mode=%d",
                                           this.id,
                                           message.getBodyLength(),
                                           message.getJMSDeliveryMode(),
                                           message.getJMSPriority(),
                                           message.getJMSExpiration(),
                                           session.getTransacted(),
                                           session.getAcknowledgeMode());
                System.out.println(log);

                assert transacted == session.getTransacted();
                assert acknowledgeMode == session.getAcknowledgeMode();
            }
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
