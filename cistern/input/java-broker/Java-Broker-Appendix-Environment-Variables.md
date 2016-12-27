# <span class="header-section-number">1</span> Environment Variables

The following table describes the environment variables understood by
the Qpid scripts contained within the `/bin` directory within the Broker
distribution.

To take effect, these variables must be set within the shell (and
exported - if using Unix) before invoking the script.

<table>
<caption>Environment variables</caption>
<colgroup>
<col width="33%" />
<col width="33%" />
<col width="33%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">Environment variable</th>
<th align="left">Default</th>
<th align="left">Purpose</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">QPID_HOME</td>
<td align="left"><p>None</p></td>
<td align="left"><p>The variable used to tell the Broker its installation directory. It must be an absolute path. This is used to determine the location of Qpid's dependency JARs and some configuration files.</p>
<p>Typically the value of this variable will look similar to <code>c:\qpid\WINDOWSEXTRACTEDBROKERDIRNAME</code> (Windows) or <code>/usr/local/qpid/UNIXEXTRACTEDBROKERDIRNAME</code> (Unix). The installation prefix will differ from installation to installation.</p>
<p>If not set, a value for <code>QPID_HOME</code> is derived from the location of the script itself.</p></td>
</tr>
<tr class="even">
<td align="left">QPID_WORK</td>
<td align="left"><p>User's home directory</p></td>
<td align="left"><p>Used as the default root directory for any data written by the Broker. This is the default location for any message data written to persistent stores and the Broker's log file.</p>
<p>For example, <code>QPID_WORK=/var/qpidwork</code>.</p></td>
</tr>
<tr class="odd">
<td align="left">QPID_OPTS</td>
<td align="left"><p>None</p></td>
<td align="left"><p>This is the preferred mechanism for passing Java <a href="#Java-Broker-Appendix-System-Properties">system properties</a> to the Broker. The value must be a list of system properties each separate by a space. <code>-Dname1=value1                   -Dname2=value2</code>.</p></td>
</tr>
<tr class="even">
<td align="left">QPID_JAVA_GC</td>
<td align="left"><code>-XX:+HeapDumpOnOutOfMemoryError -XX:+UseConcMarkSweepGC</code></td>
<td align="left"><p>This is the preferred mechanism for customising garbage collection behaviour. The value should contain valid garbage collection options(s) for the target JVM.</p>
<p>Refer to the JVM's documentation for details.</p></td>
</tr>
<tr class="odd">
<td align="left">QPID_JAVA_MEM</td>
<td align="left"><code>-Xmx2g</code></td>
<td align="left"><p>This is the preferred mechanism for customising the size of the JVM's heap memory. The value should contain valid memory option(s) for the target JVM. Oracle JVMs understand <code>-Xmx</code> to specify a maximum heap size and <code>-Xms</code> an initial size.</p>
<p>For example, <code>QPID_JAVA_MEM=-Xmx6g</code> would set a maximum heap size of 6GB.</p>
<p>Refer to the JVM's documentation for details.</p></td>
</tr>
<tr class="even">
<td align="left">JAVA_OPTS</td>
<td align="left">None</td>
<td align="left"><p>This is the preferred mechanism for passing any other JVM options. This variable is commonly used to pass options for diagnostic purposes, for instance to turn on verbose GC. <code>-verbose:gc</code>.</p>
<p>Refer to the JVM's documentation for details.</p></td>
</tr>
</tbody>
</table>


