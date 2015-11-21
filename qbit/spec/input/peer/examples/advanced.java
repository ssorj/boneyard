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

import qpid.peer;
import java.util.HashSet;

//
// Sending peer
//

class SendingPeer
{
    public static void main(String[] args)
    {
        Home home = new Home();

        Connector conn1 = new TcpConnector(home, "alpha.example.net");
        Connector conn2 = new TcpConnector(home, "beta.example.net", "5673");

        home.setSyncSend(false);
        home.setAutoSettle(false);

        home.createTarget("queue1", conn1);
        home.createTarget("queue2", conn2);

        try {
            conn1.connect();
        } catch (ConnectionError e) {
            System.err.println("Encountered a connection error: " + e);
            throw e
        }

        Message message = new Message();
        Set deliveries = new HashSet();
        int count = 10;

        while (count > 0) {
            Event event = home.nextEvent(Target.class);
            Target target = event.getTarget();

            count -= 1;

            message.setContent(count);

            Delivery delivery = target.send(message);

            deliveries.add(delivery);
        }

        while (deliveries.size() > 0) {
            Event event = home.nextEvent(Delivery.class);
            Delivery delivery = event.getDelivery();
            
            if (delivery.getDisposition() == Disposition.ACCEPTED) {
                delivery.settle();
                deliveries.remove(delivery);
            }
        }
    }
}

// 
// Receiving peer
//

class ReceivingPeer
{
    public static void main(String[] args)
    {
        Home home = Home();
        home.setSyncAcknowledge(false);

        home.createSource("queue1");
        home.createSource("queue2");

        Message message = new Message();
        Set deliveries = new HashSet();
        int count = 10;

        while (count > 0) {
            Event event = home.nextEvent(Source.class);
            Source source = event.getSource();

            Delivery delivery = source.receive(message);

            System.out.println(message.getContent());

            deliveries.add(delivery);

            count -= 1;

            delivery.acknowledge(Disposition.ACCEPTED);
        }

        while (deliveries.size() > 0) {
            Event event = home.nextEvent(Delivery.class);
            Delivery delivery = event.getDelivery();

            if (delivery.isSettled()) {
                delivery.settle();
                deliveries.remove(delivery);
            }
        }
    }
}
