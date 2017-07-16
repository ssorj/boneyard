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
var url = require("url");

function parse_url(s) {
    var u = url.parse(s, false, true);
    var host = u.hostname;
    var port = u.port;
    var path = u.pathname;

    if (!path) {
        throw new Error("No path!");
    }

    if (!host) {
        host = "127.0.0.1";
    }

    if (!port) {
        port = "5672";
    }

    if (path.startsWith("/")) {
        path = path.slice(1);
    }

    return [host, port, path];
}

var [host, port, path] = parse_url(process.argv[2]);
var container = rhea.create_container();

container.on("connection_open", function (context) {
    context.connection.open_receiver(path);
    console.log("morty: Created receiver for source address '" + path + "'");
});

container.on("message", function (context) {
    var request = context.message;
    var reply_to = request.reply_to;

    console.log("morty: Received request '" + request.body + "'");

    var response = {
        to: reply_to,
        body: request.body.toString().toUpperCase()
    };

    if (request.correlation_id) {
        response.correlation_id = request.correlation_id;
    }

    context.connection.send(response);

    console.log("morty: Sent response '" + response.body + "'");
});

container.connect({username: "anonymous", host: host, port: port});
