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

import java.net.MalformedURLException;
import java.net.URL;
import java.util.UUID;
import org.arquillian.cube.openshift.impl.enricher.AwaitRoute;
import org.arquillian.cube.openshift.impl.enricher.RouteURL;
import org.jboss.arquillian.junit.Arquillian;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import static com.jayway.restassured.RestAssured.given;

@RunWith(Arquillian.class)
public class OpenShiftIT {
    @RouteURL("frontend")
    @AwaitRoute(path = "/health")
    private URL frontendUrl;

    private URL dataUrl;
    private URL requestUrl;

    @Before
    public void before() throws MalformedURLException {
        dataUrl = new URL(frontendUrl, "api/data");
        requestUrl = new URL(frontendUrl, "api/send-request");
    }

    @Test
    public void testRequestProcessing() {
        String text = UUID.randomUUID().toString();
        String json = String.format("{'text': '%s'}", text);

        given().body(text)
            .contentType("application/json")
            .post(requestUrl)
            .then()
            .assertThat()
            .statusCode(200);
    }
}
