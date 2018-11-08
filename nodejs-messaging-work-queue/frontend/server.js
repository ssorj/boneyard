//
// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.
//

"use strict";

const body_parser = require("body-parser");
const crypto = require("crypto");
const express = require("express");
const probe = require("kube-probe");
const rhea = require("rhea");

const amqp_host = process.env.MESSAGING_SERVICE_HOST || "localhost";
const amqp_port = process.env.MESSAGING_SERVICE_PORT || 5672;
const amqp_user = process.env.MESSAGING_SERVICE_USER || "work-queue";
const amqp_password = process.env.MESSAGING_SERVICE_PASSWORD || "work-queue";

const http_host = process.env.IP || process.env.OPENSHIFT_NODEJS_IP || "0.0.0.0";
const http_port = process.env.PORT || process.env.OPENSHIFT_NODEJS_PORT || 8080;

// AMQP

const id = "frontend-nodejs-" + crypto.randomBytes(2).toString("hex");
const container = rhea.create_container({id: id});

let request_sender = null;
let response_receiver = null;
let worker_update_receiver = null;

const request_messages = [];
const request_ids = [];
const responses = {};
const workers = {};

let request_sequence = 0;

function send_requests() {
    if (!response_receiver) {
        return;
    }

    while (request_sender.sendable() && request_messages.length > 0) {
        let message = request_messages.shift();
        message.reply_to = response_receiver.source.address;

        request_sender.send(message);

        console.log("%s: Sent request %s", id, JSON.stringify(message));
    }
}

container.on("connection_open", (event) => {
    console.log("%s: Connected to AMQP messaging service at %s:%s", id, amqp_host, amqp_port);

    request_sender = event.connection.open_sender("work-queue/requests");
    response_receiver = event.connection.open_receiver({source: {dynamic: true}});
    worker_update_receiver = event.connection.open_receiver("work-queue/worker-updates");
});

container.on("sendable", (event) => {
    send_requests();
});

container.on("message", (event) => {
    if (event.receiver === worker_update_receiver) {
        let update = event.message.application_properties;

        workers[update.workerId] = {
            workerId: update.workerId,
            timestamp: update.timestamp,
            requestsProcessed: update.requestsProcessed,
            processingErrors: update.processingErrors,
        };

        return;
    }

    if (event.receiver === response_receiver) {
        let response = event.message;

        console.log("%s: Received response %s", id, response);

        responses[response.correlation_id] = {
            requestId: response.correlation_id,
            workerId: response.application_properties.workerId,
            text: response.body,
        };

        return;
    }

    throw new Exception();
});

const opts = {
    host: amqp_host,
    port: amqp_port,
    username: amqp_user,
    password: amqp_password,
};

container.connect(opts);

// HTTP

const app = express();

app.use(express.static("static"));
app.use(body_parser.json());

probe(app)

app.post("/api/send-request", (req, resp) => {
    let message = {
        message_id: `${id}/${request_sequence++}`,
        application_properties: {
            uppercase: req.body.uppercase,
            reverse: req.body.reverse,
        },
        body: req.body.text,
    };

    request_messages.push(message);
    request_ids.push(message.message_id);

    send_requests();

    resp.status(202).send(message.message_id);
});

app.get("/api/receive-response", (req, resp) => {
    let request_id = req.query.request;

    if (request_id == null) {
        resp.status(500).end();
        return;
    }

    let response = responses[request_id];

    if (response == null) {
        resp.status(404).end();
        return;
    }

    resp.json(response);
});

app.get("/api/data", (req, resp) => {
    resp.json({
        requestIds: request_ids,
        responses: responses,
        workers: workers
    });
});

app.listen(http_port, http_host);

console.log("%s: Listening for new HTTP connections at %s:%s", id, http_host, http_port);

function pruneStaleWorkers() {
    for (let workerId of Object.keys(workers)) {
        let now = new Date().getTime();

        let update = workers[workerId];

        if (now - update.timestamp > 10 * 1000) {
            delete workers[workerId];
            console.log("%s: Pruned %s", id, workerId);
        }
    }
}

setInterval(pruneStaleWorkers, 5 * 1000);
