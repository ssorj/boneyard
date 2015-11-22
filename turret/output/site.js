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

"use strict";

var $ = function(selectors) {
    return document.querySelector(selectors);
};

var turret = {
    unmarshalQueryVars: function() {
        var vars = {};
        
        location.search.substr(1).split(";").forEach(function(item) {
            var pair = item.split("=");
            var key = pair[0];
            var value = pair[1] && decodeURIComponent(pair[1]);

            if (key in vars) {
                vars[key].push(value);
            } else {
                vars[key] = [value];
            }
        });

        return vars;
    },
    
    marshalQueryVars: function(vars) {
        var out = [];

        for (var key in vars) {
            out.push(encodeURIComponent(key) + "=" + encodeURIComponent(vars[key]));
        }

        return out.join(";");
    },

    sendProcedureCall: function(name, args, handler) {
        var request = new XMLHttpRequest();
        var sargs = this.marshalQueryVars(args);
        var url = "/_procedures/" + name + "?" + sargs;
        
        request.onreadystatechange = function() {
            if (request.readyState == 4 && request.status == 200) {
                var data = JSON.parse(request.responseText);
                handler(data);
            }
        };

        request.open("GET", url);
        request.send(null);
    },

    appendChildLink: function(elem, href, content) {
        var child = document.createElement("a");

        child.setAttribute("href", href);
        child.textContent = content

        elem.appendChild(child);
    }
};
