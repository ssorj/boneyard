# <span class="header-section-number">1</span> Connection URLs

In JNDI properties, a Connection URL specifies options for a connection.
The format for a Connection URL is:

    amqp://[<user>:<pass>@][<clientid>]/[<virtualhost>][?<option>='<value>'[&<option>='<value>']*]

For instance, the following Connection URL specifies a user name, a
password, a client ID, a virtual host ("test"), a broker list with a
single broker: a TCP host with the host name “localhost” using port
5672:

    amqp://username:password@clientid/test?brokerlist='tcp://localhost:5672'

> **Important**
>
> Take care with the quoting surrounding option values. Each option
> value *must* be surrounded with single quotes (').

The Connection URL supports the following options:

<table>
<caption>Connection URL Options</caption>
<colgroup>
<col width="33%" />
<col width="33%" />
<col width="33%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">Option</th>
<th align="left">Type</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">brokerlist</td>
<td align="left">see below</td>
<td align="left">List of one or more broker addresses.</td>
</tr>
<tr class="even">
<td align="left">maxprefetch</td>
<td align="left">integer</td>
<td align="left"><p>The maximum number of pre-fetched messages per Session. If not specified, default value of 500 is used.</p>
<p>Note: You can also set the default per-session prefetch value on a client-wide basis by configuring the client using <a href="#JMS-Client-0-8-System-Properties">Java system properties.</a></p></td>
</tr>
<tr class="odd">
<td align="left">sync_publish</td>
<td align="left">String</td>
<td align="left"><p>If the value is 'all' the client library waits for confirmation before returning from a send(), and if the send is unsuccessful the send() will throw a JMSException. (Note this option requires an extension to the AMQP protocol and will only work against a broker of the 0.32 release or later.)</p></td>
</tr>
<tr class="even">
<td align="left">sync_ack</td>
<td align="left">Boolean</td>
<td align="left">A sync command is sent after every acknowledgement to guarantee that it has been received.</td>
</tr>
<tr class="odd">
<td align="left">use_legacy_map_msg_format</td>
<td align="left">Boolean</td>
<td align="left">If you are using JMS Map messages and deploying a new client with any JMS client older than 0.8 release, you must set this to true to ensure the older clients can understand the map message encoding.</td>
</tr>
<tr class="even">
<td align="left">failover</td>
<td align="left">{'singlebroker' | 'roundrobin' , | 'nofailover' | '&lt;class&gt;'}</td>
<td align="left"><p>This option controls failover behaviour. The method <code>singlebroker</code> uses only the first broker in the list, <code>roundrobin</code> will try each broker given in the broker list until a connection is established, <code>nofailover</code> disables all retry and failover logic. Any other value is interpreted as a classname which must implement the <code>org.apache.qpid.jms.failover.FailoverMethod</code> interface.</p>
<p>The broker list options <code>retries</code> and <code>connectdelay</code> (described below) determine the number of times a connection to a broker will be retried and the length of time to wait between successive connection attempts before moving on to the next broker in the list. The failover option <code>cyclecount</code> controls the number of times to loop through the list of available brokers before finally giving up.</p>
<p>Defaults to <code>roundrobin</code> if the brokerlist contains multiple brokers, or <code>singlebroker</code> otherwise.</p></td>
</tr>
<tr class="odd">
<td align="left">closeWhenNoRoute</td>
<td align="left">boolean</td>
<td align="left"><p>See ?.</p></td>
</tr>
<tr class="even">
<td align="left">ssl</td>
<td align="left">boolean</td>
<td align="left"><p>If <code>ssl='true'</code>, use SSL for all broker connections. Overrides any per-broker settings in the brokerlist (see below) entries. If not specified, the brokerlist entry for each given broker is used to determine whether SSL is used.</p>
<p>Introduced in version 0.22.</p></td>
</tr>
<tr class="odd">
<td align="left">compressMessages</td>
<td align="left">Boolean</td>
<td align="left"><p>Controls whether the client will compress messages before they they are sent.</p></td>
</tr>
<tr class="even">
<td align="left">messageCompressionThresholdSize</td>
<td align="left">Integer</td>
<td align="left"><p>The payload size beyond which the client will start to compress message payloads.</p></td>
</tr>
</tbody>
</table>

Broker lists are specified using a URL in this format:

    brokerlist='<transport>://<host>[:<port>][?<param>='<value>'[&<param>='<value>']*]'

For instance, this is a typical broker list:

    brokerlist='tcp://localhost:5672'

A broker list can contain more than one broker address separated by
semicolons (;). If so, the connection is made to the first broker in the
list that is available.

A broker list can specify properties to be used when connecting to the
broker. This broker list specifies options for configuring heartbeating

    amqp://guest:guest@test/test?brokerlist='tcp://ip1:5672?heartbeat='5''

This broker list specifies some SSL options

    amqp://guest:guest@test/test?brokerlist='tcp://ip1:5672?ssl='true'&ssl_cert_alias='cert1''

This broker list specifies two brokers using the connectdelay and
retries broker options. It also illustrates the failover connection URL
property.

    amqp://guest:guest@/test?failover='roundrobin?cyclecount='2''
          &brokerlist='tcp://ip1:5672?retries='5'&connectdelay='2000';tcp://ip2:5672?retries='5'&connectdelay='2000''
          

> **Important**
>
> Take care with the quoting surrounding broker option values. Each
> broker option value *must* be surrounded with their own single quotes
> ('). This is in addition to the quotes surround the connection option
> value.

The following broker list options are supported.

<table>
<caption>Broker List Options</caption>
<colgroup>
<col width="33%" />
<col width="33%" />
<col width="33%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">Option</th>
<th align="left">Type</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">heartbeat</td>
<td align="left">Long</td>
<td align="left">Frequency of heartbeat messages (in seconds). A value of 0 disables heartbeating.
<p>For compatibility with old client configuration, option <code>idle_timeout</code> (in milliseconds) is also supported.</p></td>
</tr>
<tr class="even">
<td align="left">ssl</td>
<td align="left">Boolean</td>
<td align="left"><p>If <code>ssl='true'</code>, the JMS client will encrypt the connection to this broker using SSL.</p>
<p>This can also be set/overridden for all brokers using the Connection URL option <code>ssl</code>.</p></td>
</tr>
<tr class="odd">
<td align="left">trust_store</td>
<td align="left">String</td>
<td align="left">Path to trust store. Used when using SSL and the Broker's certificate is signed by a private-CA (or a self-signed certificate),</td>
</tr>
<tr class="even">
<td align="left">trust_store_password</td>
<td align="left">String</td>
<td align="left">Trust store password. Password used to open the trust store.</td>
</tr>
<tr class="odd">
<td align="left">trusted_certs_path</td>
<td align="left">String</td>
<td align="left">Path to a file containing trusted peer certificates(in PEM or DER format). Used when supplying the trust information for TLS client auth using PEM/DER files rather than a Java KeyStore.</td>
</tr>
<tr class="even">
<td align="left">key_store</td>
<td align="left">String</td>
<td align="left">Path to key store . Used when using SSL and the client must authenticate using client-auth. If the store contains more than one certificate, <code>ssl_cert_alias</code> must be used to identify the certificate that the client must present to the Broker.</td>
</tr>
<tr class="odd">
<td align="left">key_store_password</td>
<td align="left">String</td>
<td align="left">Key store password. Password used to open the key store.</td>
</tr>
<tr class="even">
<td align="left">client_cert_path</td>
<td align="left">String</td>
<td align="left">Path to the client certificate file (in PEM or DER format). Used as an alternative to using a Java KeyStore to hold key information for TLS client auth. When used, the <code>client_cert_priv_key_path</code> must also be supplied.</td>
</tr>
<tr class="odd">
<td align="left">client_cert_priv_key_path</td>
<td align="left">String</td>
<td align="left">Path to the client certificate private key file (in PEM or DER format). Used when supplying the key information for TLS client auth using PEM/DER files rather than a Java KeyStore.</td>
</tr>
<tr class="even">
<td align="left">client_cert_intermediary_cert_path</td>
<td align="left">String</td>
<td align="left">Path to a file containing any intermediary certificates (in PEM or DER format). Used when supplying the key information for TLS client auth using PEM/DER files rather than a Java KeyStore. Only required where intermediary certificates are required in the certificate chain.</td>
</tr>
<tr class="odd">
<td align="left">ssl_cert_alias</td>
<td align="left">String</td>
<td align="left">If multiple certificates are present in the keystore, the alias will be used to extract the correct certificate.</td>
</tr>
<tr class="even">
<td align="left">ssl_verify_hostname</td>
<td align="left">Boolean</td>
<td align="left">This option is used for turning on/off hostname verification when using SSL. It is set to 'true' by default. You can disable verification by setting it to 'false': <code>ssl_verify_hostname='false'</code>.</td>
</tr>
<tr class="odd">
<td align="left">retries</td>
<td align="left">Integer</td>
<td align="left">The number of times to retry connection to each broker in the broker list. Defaults to 1.</td>
</tr>
<tr class="even">
<td align="left">connectdelay</td>
<td align="left">integer</td>
<td align="left">Length of time (in milliseconds) to wait before attempting to reconnect. Defaults to 0.</td>
</tr>
<tr class="odd">
<td align="left">connecttimeout</td>
<td align="left">integer</td>
<td align="left">Length of time (in milliseconds) to wait for the socket connection to succeed. A value of 0 represents an infinite timeout, i.e. the connection attempt will block until established or an error occurs. Defaults to 30000.</td>
</tr>
<tr class="even">
<td align="left">tcp_nodelay</td>
<td align="left">Boolean</td>
<td align="left">If <code>tcp_nodelay='true'</code>, TCP packet batching is disabled. Defaults to true since Qpid 0.14.</td>
</tr>
</tbody>
</table>


