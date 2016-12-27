# <span class="header-section-number">1</span> Message Compression

The Java Broker supports<span id="fnref1">[^1^](#fn1)</span> message
compression. This feature works in co-operation with Qpid Clients
implementing the same feature.

Once the feature is enabled (using Broker context variable
*broker.messageCompressionEnabled*), the Broker will advertise support
for the message compression feature to the client at connection time.
This allows clients to opt to turn on message compression, allowing
message payload sizes to be reduced.

If the Broker has connections from clients who have message compression
enabled and others who do not, it will internally, on-the-fly,
decompress compressed messages when sending to clients without support
and conversely, compress uncomressed messages when sending to clients
who do.

The Broker has a threshold below which it will not consider compressing
a message, this is controlled by Broker content variable
(`connection.messageCompressionThresholdSize`) and expresses a size in
bytes.

This feature *may* have a beneficial effect on performance by:

-   Reducing the number of bytes transmitted over the wire, both between
    Client and Broker, and in the HA case, Broker to Broker, for
    replication purposes.

-   Reducing storage space when data is at rest within the Broker, both
    on disk and in memory.

Of course, compression and decompression is computationally expensive.
Turning on the feature may have a negative impact on CPU utilization on
Broker and/or Client. Also for small messages payloads, message
compression may increase the message size. It is recommended to test the
feature with representative data.

------------------------------------------------------------------------

1.  <div id="fn1">

    </div>

    Message compression is not yet supported for the 1.0
    protocol.[↩](#fnref1)


