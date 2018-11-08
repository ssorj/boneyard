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

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.vertx.core.Vertx;
import io.vertx.core.logging.Logger;
import io.vertx.core.logging.LoggerFactory;
import io.vertx.ext.web.Router;
import io.vertx.ext.web.RoutingContext;
import io.vertx.ext.web.handler.BodyHandler;
import io.vertx.ext.web.handler.StaticHandler;
import io.vertx.proton.ProtonClient;
import io.vertx.proton.ProtonConnection;
import io.vertx.proton.ProtonReceiver;
import io.vertx.proton.ProtonSender;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Queue;
import java.util.UUID;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.qpid.proton.amqp.messaging.AmqpValue;
import org.apache.qpid.proton.amqp.messaging.ApplicationProperties;
import org.apache.qpid.proton.amqp.messaging.Section;
import org.apache.qpid.proton.amqp.messaging.Source;
import org.apache.qpid.proton.message.Message;

import static io.vertx.core.http.HttpHeaders.CONTENT_TYPE;

public class Frontend {
    private static final Logger log = LoggerFactory.getLogger(Frontend.class);
    private static final String id = "frontend-vertx-" + UUID.randomUUID()
        .toString().substring(0, 4);
    private static final ObjectMapper mapper = new ObjectMapper();

    private static ProtonSender requestSender;
    private static ProtonReceiver responseReceiver;

    private static final AtomicInteger requestSequence = new AtomicInteger(0);
    private static final Queue<Message> requestMessages = new ConcurrentLinkedQueue<>();
    private static final Data data = new Data();

    public static void main(String[] args) {
        try {
            String amqpHost = System.getenv("MESSAGING_SERVICE_HOST");
            String amqpPortString = System.getenv("MESSAGING_SERVICE_PORT");
            String amqpUser = System.getenv("MESSAGING_SERVICE_USER");
            String amqpPassword = System.getenv("MESSAGING_SERVICE_PASSWORD");

            String httpHost = System.getenv("HTTP_HOST");
            String httpPortString = System.getenv("HTTP_PORT");

            if (amqpHost == null) {
                amqpHost = "localhost";
            }

            if (amqpPortString == null) {
                amqpPortString = "5672";
            }

            if (amqpUser == null) {
                amqpUser = "work-queue";
            }

            if (amqpPassword == null) {
                amqpPassword = "work-queue";
            }

            if (httpHost == null) {
                httpHost = "0.0.0.0";
            }

            if (httpPortString == null) {
                httpPortString = "8080";
            }

            int amqpPort = Integer.parseInt(amqpPortString);
            int httpPort = Integer.parseInt(httpPortString);

            // AMQP

            Vertx vertx = Vertx.vertx();
            ProtonClient client = ProtonClient.create(vertx);

            client.connect(amqpHost, amqpPort, amqpUser, amqpPassword, (result) -> {
                    if (result.failed()) {
                        result.cause().printStackTrace();
                        return;
                    }

                    ProtonConnection conn = result.result();
                    conn.setContainer(id);
                    conn.open();

                    sendRequests(vertx, conn);
                    receiveWorkerUpdates(vertx, conn);
                    pruneStaleWorkers(vertx);
                });

            // HTTP

            Router router = Router.router(vertx);

            router.route().handler(BodyHandler.create());
            router.post("/api/send-request").handler(Frontend::handleSendRequest);
            router.get("/api/receive-response").handler(Frontend::handleReceiveResponse);
            router.get("/api/data").handler(Frontend::handleGetData);
            router.get("/api/health/readiness").handler(Frontend::handleGetReadiness);
            router.get("/api/health/liveness").handler(Frontend::handleGetLiveness);
            router.get("/*").handler(StaticHandler.create());

            vertx.createHttpServer()
                .requestHandler(router::accept)
                .listen(httpPort, httpHost, (result) -> {
                        if (result.failed()) {
                            result.cause().printStackTrace();
                            return;
                        }
                    });

            while (true) {
                Thread.sleep(60 * 1000);
            }
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    private static void sendRequests(Vertx vertx, ProtonConnection conn) {
        requestSender = conn.createSender("work-queue/requests");

        // Using a null address and setting the source dynamic tells
        // the remote peer to generate the reply address.
        responseReceiver = conn.createReceiver(null);
        Source source = (Source) responseReceiver.getSource();
        source.setDynamic(true);

        responseReceiver.openHandler((result) -> {
                requestSender.sendQueueDrainHandler((s) -> {
                        doSendRequests();
                    });
            });

        responseReceiver.handler((delivery, message) -> {
                Map props = message.getApplicationProperties().getValue();
                String workerId = (String) props.get("workerId");
                String requestId = (String) message.getCorrelationId();
                String text = (String) ((AmqpValue) message.getBody()).getValue();
                Response response = new Response(requestId, workerId, text);

                data.getResponses().put(response.getRequestId(), response);

                log.info("{0}: Received {1}", id, response);
            });

        requestSender.open();
        responseReceiver.open();
    }

    private static void doSendRequests() {
        if (responseReceiver == null) {
            return;
        }

        if (responseReceiver.getRemoteSource().getAddress() == null) {
            return;
        }

        while (!requestSender.sendQueueFull()) {
            Message message = requestMessages.poll();

            if (message == null) {
                break;
            }

            message.setReplyTo(responseReceiver.getRemoteSource().getAddress());

            requestSender.send(message);

            log.info("{0}: Sent {1}", id, message);
        }
    }

    private static void receiveWorkerUpdates(Vertx vertx, ProtonConnection conn) {
        ProtonReceiver receiver = conn.createReceiver("work-queue/worker-updates");

        receiver.handler((delivery, message) -> {
                Map props = message.getApplicationProperties().getValue();
                String workerId = (String) props.get("workerId");
                long timestamp = (long) props.get("timestamp");
                long requestsProcessed = (long) props.get("requestsProcessed");
                long processingErrors = (long) props.get("processingErrors");

                WorkerUpdate update = new WorkerUpdate(workerId, timestamp, requestsProcessed,
                                                       processingErrors);

                data.getWorkers().put(update.getWorkerId(), update);
            });

        receiver.open();
    }

    private static void handleSendRequest(RoutingContext rc) {
        String json = rc.getBodyAsString();
        String requestId = id + "/" + requestSequence.incrementAndGet();
        Request request;

        try {
            request = mapper.readValue(json, Request.class);
        } catch (IOException e) {
            rc.fail(e);
            return;
        }

        Map<String, Object> props = new HashMap<String, Object>();
        props.put("uppercase", request.isUppercase());
        props.put("reverse", request.isReverse());

        Message message = Message.Factory.create();
        message.setMessageId(requestId);
        message.setAddress("work-queue/requests");
        message.setBody(new AmqpValue(request.getText()));
        message.setApplicationProperties(new ApplicationProperties(props));

        requestMessages.add(message);

        data.getRequestIds().add(requestId);

        doSendRequests();

        rc.response().setStatusCode(202).end(requestId);
    }

    private static void handleReceiveResponse(RoutingContext rc) {
        List<String> values = rc.queryParam("request");

        if (values.size() != 1) {
            rc.fail(500);
            return;
        }

        Response response = data.getResponses().get(values.get(0));

        if (response == null) {
            rc.response().setStatusCode(404).end();
            return;
        }

        String json;

        try {
            json = mapper.writeValueAsString(response);
        } catch (JsonProcessingException e) {
            rc.fail(e);
            return;
        }

        rc.response()
            .setStatusCode(200)
            .putHeader(CONTENT_TYPE, "application/json; charset=utf-8")
            .end(json);
    }

    private static void handleGetData(RoutingContext rc) {
        String json;

        try {
            json = mapper.writeValueAsString(data);
        } catch (JsonProcessingException e) {
            rc.fail(e);
            return;
        }

        rc.response()
            .putHeader(CONTENT_TYPE, "application/json; charset=utf-8")
            .end(json);
    }

    private static void handleGetReadiness(RoutingContext rc) {
        rc.response().end("OK");
    }

    private static void handleGetLiveness(RoutingContext rc) {
        rc.response().end("OK");
    }

    private static void pruneStaleWorkers(Vertx vertx) {
        vertx.setPeriodic(5 * 1000, (timer) -> {
                log.debug("{0}: Pruning stale workers", id);

                Map<String, WorkerUpdate> workers = data.getWorkers();
                long now = System.currentTimeMillis();

                for (Map.Entry<String, WorkerUpdate> entry : workers.entrySet()) {
                    String workerId = entry.getKey();
                    WorkerUpdate update = entry.getValue();

                    if (now - update.getTimestamp() > 10 * 1000) {
                        workers.remove(workerId);
                        log.info("{0}: Pruned {1}", id, workerId);
                    }
                }
            });
    }
}
