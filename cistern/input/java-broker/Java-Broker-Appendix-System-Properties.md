# <span class="header-section-number">1</span> System Properties

The following table describes the Java system properties used by the
Broker to control various optional behaviours.

The preferred method of enabling these system properties is using the
[`QPID_OPTS`](#Java-Broker-Appendix-Environment-Variables-Qpid-Opts)
environment variable described in the previous section.

<table>
<caption>System properties</caption>
<colgroup>
<col width="33%" />
<col width="33%" />
<col width="33%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">System property</th>
<th align="left">Default</th>
<th align="left">Purpose</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">qpid.broker_heartbeat_timeout_factor</td>
<td align="left">2</td>
<td align="left">Factor to determine the maximum length of that may elapse between heartbeats being received from the peer before a connection is deemed to have been broken.</td>
</tr>
<tr class="even">
<td align="left">qpid.broker_dead_letter_exchange_suffix</td>
<td align="left">_DLE</td>
<td align="left">Used with the ? feature. Governs the suffix used when generating a name for a Dead Letter Exchange.</td>
</tr>
<tr class="odd">
<td align="left">qpid.broker_dead_letter_queue_suffix</td>
<td align="left">_DLQ</td>
<td align="left">Used with the ? feature. Governs the suffix used when generating a name for a Dead Letter Queue.</td>
</tr>
<tr class="even">
<td align="left">qpid.broker_msg_auth</td>
<td align="left">false</td>
<td align="left"><p>If set true, the Broker ensures that the user id of each received message matches the user id of the producing connection. If this check fails, the message is returned to the producer's connection with a 403 (Access Refused) error code.</p>
<p>This is check is currently not enforced when using AMQP 0-10 and 1-0 protocols.</p></td>
</tr>
<tr class="odd">
<td align="left">qpid.broker_status_updates</td>
<td align="left">true</td>
<td align="left"><p>If set true, the Broker will produce operational logging messages.</p></td>
</tr>
<tr class="even">
<td align="left">qpid.broker_default_supported_protocol_version_reply</td>
<td align="left">none</td>
<td align="left"><p>Used during protocol negotiation. If set, the Broker will offer this AMQP version to a client requesting an AMQP protocol that is not supported by the Broker. If not set, the Broker offers the highest protocol version it supports.</p></td>
</tr>
<tr class="odd">
<td align="left">qpid.broker_disabled_features</td>
<td align="left">none</td>
<td align="left"><p>Allows optional Broker features to be disabled. Currently understood feature names are: <code>qpid.jms-selector</code></p>
<p>Feature names should be comma separated.</p></td>
</tr>
<tr class="even">
<td align="left">qpid.broker_frame_size</td>
<td align="left">65536</td>
<td align="left"><p>Maximum AMQP frame size supported by the Broker.</p></td>
</tr>
<tr class="odd">
<td align="left">qpid.broker_jmx_method_rights_infer_all_access</td>
<td align="left">true</td>
<td align="left"><p>Used when using <a href="#Java-Broker-Security-ACLs">ACLs</a> and the JMX management interface.</p>
<p>If set true, the METHOD object permission is sufficient to allow the user to perform the operation. If set false, the user will require both the METHOD object permission and the underlying object permission too (for instance QUEUE object permission if performing management operations on a queue). If the user is not granted both permissions, the operation will be denied.</p></td>
</tr>
<tr class="even">
<td align="left">qpid.broker_jmx_use_custom_rmi_socket_factory</td>
<td align="left">true</td>
<td align="left"><p>Applicable to the JMX management interface. If true, the Broker creates a custom RMI socket factory that is secured from changes outside of the JVM. If false, a standard RMI socket factory is used.</p>
<p>It is not recommended to change this property from its default value.</p></td>
</tr>
<tr class="odd">
<td align="left">qpid.broker_log_records_buffer_size</td>
<td align="left">4096</td>
<td align="left"><p>Controls the number of recent Broker log entries that remain viewable online via the HTTP Management interface.</p></td>
</tr>
</tbody>
</table>


