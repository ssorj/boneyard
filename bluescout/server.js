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

const express = require("express");

const http_host = process.env.IP || process.env.OPENSHIFT_NODEJS_IP || "0.0.0.0";
const http_port = process.env.PORT || process.env.OPENSHIFT_NODEJS_PORT || 8080;

const app = express();

app.use(express.static("static"));
app.listen(http_port, http_host);

console.log("Listening for new HTTP connections at %s:%s", http_host, http_port);
