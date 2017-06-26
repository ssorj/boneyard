/*
 * Copyright 2015 Red Hat Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

"use strict";

var rhea = require("rhea");

var container = rhea.create_container();
var host = process.env.MESSAGING_SERVICE_HOST;
var address = "patient-information";

container.on("connection_open", function (context) {
    context.connection.open_receiver(address);
    console.log("patient-information: Created receiver for source address '" + address + "'");
});

container.on("message", function (context) {
    var request = context.message;
    var reply_to = request.reply_to;

    console.log("Received request: " + request.body);

    var response_body = request.body + "\nPatient Information Retrieved";
    
    var response = {
        to: reply_to,
        body: response_body
    };

    if (request.correlation_id) {
        response.correlation_id = request.correlation_id;
    }

    context.connection.send(response);
});

container.connect({username: "anonymous", host: host});
