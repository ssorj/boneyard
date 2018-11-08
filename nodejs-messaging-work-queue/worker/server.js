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

const id = "worker-nodejs-" + crypto.randomBytes(2).toString("hex");
const container = rhea.create_container({id: id});

let worker_update_sender = null;
let requests_processed = 0;
let processing_errors = 0;

function process_request(request) {
    let uppercase = request.application_properties.uppercase;
    let reverse = request.application_properties.reverse;
    let text = request.body;

    if (uppercase) {
        text = text.toUpperCase();
    }

    if (reverse) {
        text = text.split("").reverse().join("");
    }

    return text;
}

container.on("connection_open", (event) =>  {
    console.log("%s: Connected to AMQP messaging service at %s:%s", id, amqp_host, amqp_port);

    event.connection.open_receiver("work-queue/requests");
    worker_update_sender = event.connection.open_sender("work-queue/worker-updates");
});

container.on("message", (event) => {
    let request = event.message;
    let response_body;

    console.log("%s: Received request %s", id, request);

    try {
        response_body = process_request(request);
    } catch (e) {
        console.error("%s: Failed processing message: %s", id, e);
        processing_error++;
        return;
    }

    let response = {
        to: request.reply_to,
        correlation_id: request.message_id,
        application_properties: {
            workerId: container.id
        },
        body: response_body,
    };

    event.connection.send(response);

    requests_processed++;

    console.log("%s: Sent response %s", id, JSON.stringify(response));
});

function send_update() {
    if (!worker_update_sender || !worker_update_sender.sendable()) {
        return;
    }

    let update = {
        application_properties: {
            workerId: container.id,
            timestamp: new Date().getTime(),
            requestsProcessed: requests_processed,
            processingErrors: processing_errors,
        }
    };

    worker_update_sender.send(update);
}

setInterval(send_update, 5 * 1000);

const opts = {
    host: amqp_host,
    port: amqp_port,
    username: amqp_user,
    password: amqp_password,
};

container.connect(opts);

// HTTP

const app = express();

probe(app)

app.listen(http_port, http_host);

console.log("%s: Listening for new HTTP connections at %s:%s", id, http_host, http_port);
