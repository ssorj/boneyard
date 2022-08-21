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

import java.util.Hashtable;
import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;
import javax.jms.Connection;
import javax.jms.ConnectionFactory;
import javax.jms.DeliveryMode;
import javax.jms.Destination;
import javax.jms.Session;
import javax.naming.Context;
import javax.naming.InitialContext;

public class Main {
    static int[] acknowledgeModes = {
        Session.AUTO_ACKNOWLEDGE,
        Session.CLIENT_ACKNOWLEDGE,
        Session.DUPS_OK_ACKNOWLEDGE
    };

    static int[] deliveryModes = {
        DeliveryMode.PERSISTENT,
        DeliveryMode.NON_PERSISTENT
    };

    static int getAcknowledgeMode() {
        return acknowledgeModes[ThreadLocalRandom.current().nextInt(3)];
    }

    static int getDeliveryMode() {
        return deliveryModes[ThreadLocalRandom.current().nextInt(2)];
    }

    public static void main(String[] args) {
        try {
            String url = args[0];
            int numConns = 10;
            int numPairs = 10;

            Hashtable<Object, Object> env = new Hashtable<Object, Object>();
            env.put(Context.INITIAL_CONTEXT_FACTORY, "org.apache.qpid.jms.jndi.JmsInitialContextFactory");
            env.put("connectionfactory.factory1", url);
            env.put("queue.queue1", "queue1");
            env.put("topic.topic1", "topic1");

            InitialContext context = new InitialContext(env);
            ConnectionFactory factory = (ConnectionFactory) context.lookup("factory1");
            Destination queue = (Destination) context.lookup("queue1");
            Destination topic = (Destination) context.lookup("topic1");

            Connection[] conns = new Connection[numConns];
            
            for (int i = 0; i < numConns; i++) {
                conns[i] = factory.createConnection();
                conns[i].start();

                Thread[] senders = new Thread[numPairs];
                Thread[] receivers = new Thread[numPairs];

                for (int j = 0; j < numPairs; j++) {
                    String id = String.format("conn-%d/sender-%d", i, j);
                    senders[j] = new Thread(new Sender(id, conns[i], queue));
                    senders[j].setDaemon(true);
                    senders[j].start();
                }

                for (int j = 0; j < numPairs; j++) {
                    String id = String.format("conn-%d/receiver-%d", i, j);
                    receivers[j] = new Thread(new Receiver(id, conns[i], queue));
                    receivers[j].setDaemon(true);
                    receivers[j].start();
                }
            }
                
            while (true) {
                Random rng = ThreadLocalRandom.current();
                
                for (Connection conn : conns) {
                    if (rng.nextInt(10) == 0) {
                        conn.stop();
                    }
                }

                Thread.sleep(1000);

                for (Connection conn : conns) {
                    conn.start();
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }
}
