/*
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
 */

function _playDemoProvisioningLog() {
    var elem = document.getElementById("provisioning-log");

    elem.textContent += "Starting\n";

    var func = function() {
        elem.textContent += "Reticulating splines\n";
    };

    setTimeout(func, 1000);

    var func = function() {
        elem.textContent += "Flibberty jibbits!\n";
    };

    setTimeout(func, 2000);

    var func = function() {
        elem.textContent += "Done\n";
        _enableElement("continue-button");
    };

    setTimeout(func, 3000);
}
