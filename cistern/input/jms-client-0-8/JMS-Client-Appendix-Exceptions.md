# <span class="header-section-number">1</span> Exceptions

The methods of Qpid JMS Client throw
[JMSExceptions](&oracleJeeDocUrl;javax/jms/JMSException.html) in
response to error conditions. Typically the exception's message
(\#getMessage()) summarises the error condition, with contextual
information being provided by the messages of linked exception(s). To
understand the problem, it is important to read the messages associated
with *all* the linked exceptions.

The following table describes some of the more common exceptions linked
to JMSException thrown by JMS methods whilst using the client:

<table>
<caption>Exceptions linked to JMSExceptions thrown by JMS methods</caption>
<colgroup>
<col width="33%" />
<col width="33%" />
<col width="33%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">Linked Exception</th>
<th align="left">Message</th>
<th align="left">Explanation/Common Causes</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">AMQUnresolvedAddressException</td>
<td align="left"><em>message varies</em></td>
<td align="left"><p>Indicates that the hostname included in the Connection URL's <a href="#JMS-Client-0-8-Connection-URL-ConnectionOptions-Brokerlist">brokerlist</a>, could not be resolved, . This could mean that the hostname is mispelt, or there is name resolution problem.</p></td>
</tr>
<tr class="even">
<td align="left">AMQConnectionFailure</td>
<td align="left">Connection refused</td>
<td align="left"><p>Indicates that the host included in the Connection URL's <a href="#JMS-Client-0-8-Connection-URL-ConnectionOptions-Brokerlist">brokerlist</a>, actively refused the connection. This could mean that the hostname and/or port number is incorrect, or the Broker may not be running.</p></td>
</tr>
<tr class="odd">
<td align="left">AMQConnectionFailure</td>
<td align="left">connect timed out</td>
<td align="left"><p>Indicates that the host included in the Connection URL's <a href="#JMS-Client-0-8-Connection-URL-ConnectionOptions-Brokerlist">brokerlist</a>, could not be contacted within the <a href="#JMS-Client-0-8-Connection-URL-BrokerOptions-ConnectTimeout">connecttimeout</a>. This could mean that the host is shutdown, or a networking routing problem means the host is unreachable.</p></td>
</tr>
<tr class="even">
<td align="left">AMQConnectionFailure</td>
<td align="left">General SSL Problem; PKIX path building failed; unable to find valid certification path to requested target</td>
<td align="left"><p>Indicates that the CA that signed the Broker's certificate is not trusted by the JVM of the client. If the Broker is using a private-CA (or a self signed certificate) check that the client has been properly configured with a truststore. See ?</p></td>
</tr>
<tr class="odd">
<td align="left">AMQConnectionFailure / AMQAuthenticationException</td>
<td align="left">not allowed</td>
<td align="left"><p>Indicates that the user cannot be authenticated by the Broker. Check the username and/or password elements within the <a href="#JMS-Client-0-8-Connection-URL">Connection URL</a>.</p></td>
</tr>
<tr class="even">
<td align="left">AMQConnectionFailure / AMQSecurityException</td>
<td align="left">Permission denied: <em>virtualhost name</em>; access refused</td>
<td align="left"><p>Indicates that the user is not authorised to connect to the given virtualhost. The user is recognised by the Broker and is using the correct password but does not have permission. This exception normally indicates that the user (or group) has not been permissioned within the Broker's <a href="&amp;qpidJavaBrokerBook;Java-Broker-Security-ACLs.html">Access Control List (ACL)</a>.</p></td>
</tr>
<tr class="odd">
<td align="left">AMQTimeoutException</td>
<td align="left">Server did not respond in a timely fashion; Request Timeout</td>
<td align="left"><p>Indicates that the broker did not respond to a request sent by the client in a reasonable length of time. The timeout is governed by <a href="#JMS-Client-0-8-System-Properties-SyncOpTimeout"><code>qpid.sync_op_timeout</code></a>.</p>
<p>This can be a symptom of a heavily loaded broker that cannot respond or the Broker may have failed in unexpected manner. Check the broker and the host on which it runs and performance of its storage.</p></td>
</tr>
<tr class="even">
<td align="left">AMQSecurityException</td>
<td align="left">Permission denied: <em>message varies</em></td>
<td align="left"><p>Indicates that the user is not authorised to use the given resource or perform the given operation. This exception normally indicates that the user (or group) has not been permissioned within the Broker's <a href="&amp;qpidJavaBrokerBook;Java-Broker-Security-ACLs.html">Access Control List (ACL)</a>.</p></td>
</tr>
</tbody>
</table>

The following table describes some of the more common exceptions linked
to JMSException sent to
[ExceptionListener](&oracleJeeDocUrl;javax/jmx/ExceptionListener.html)
instances.

<table>
<caption>Exceptions linked to JMSExceptions received by ExceptionListeners</caption>
<colgroup>
<col width="33%" />
<col width="33%" />
<col width="33%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">Linked Exception</th>
<th align="left">Message</th>
<th align="left">Explanation/Common Causes</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">AMQNoRouteException</td>
<td align="left">No Route for message [Exchange: <em>exchange name</em>, Routing key: <em>routing key</em>] [error code 312: no route]</td>
<td align="left"><p>Indicate that the named exchange is unable to route a message to at least one queue.</p>
<p>This will occur if a queue has been improperly bound to an exchange. Use the Broker's management interface to check the bindings. See ?</p></td>
</tr>
<tr class="even">
<td align="left">AMQNoConsumersException</td>
<td align="left">Immediate delivery is not possible. [error code 313: no consumers]</td>
<td align="left"><p>Immediate delivery was requested by the MessageProducer, but as there are no consumers on any target queue, the message has been returned to the publisher. See ?</p></td>
</tr>
<tr class="odd">
<td align="left">AMQDisconnectedException</td>
<td align="left">Server closed connection and reconnection not permitted</td>
<td align="left"><p>Indicates that the connection was closed by the Broker, and as <a href="#JMS-Client-0-8-Client-Understanding-Connection-Failover">failover options</a> are not included in the Connection URL, the client has been unable to reestablish connection.</p>
<p>The Connection is now closed and any attempt to use either Connection object, or any objects created from the Connection will receive an <a href="&amp;oracleJeeDocUrl;javax/jms/IllegalStateException.html">IllegalStateException</a>.</p></td>
</tr>
<tr class="even">
<td align="left">AMQDisconnectedException</td>
<td align="left">Server closed connection and no failover was successful</td>
<td align="left"><p>Indicates that the connection was closed by the Broker. The client has tried failover according to the rules of the <a href="#JMS-Client-0-8-Client-Understanding-Connection-Failover">failover options</a>within the Connection URL, but these attempts were all unsuccessful.</p>
<p>The Connection is now closed and any attempt to use either Connection object, or any objects created from the Connection will receive an <a href="&amp;oracleJeeDocUrl;javax/jms/IllegalStateException.html">IllegalStateException</a>.</p></td>
</tr>
</tbody>
</table>


