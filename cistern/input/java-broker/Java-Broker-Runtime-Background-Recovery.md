# <span class="header-section-number">1</span> Background Recovery

On startup of the Broker, or restart of a Virtualhost, the Broker
restores all durable queues and their messages from disk. In the
Broker's default mode the Virtualhosts do not become active until this
recovery process completes. If queues have a large number of entries,
this may take considerable time. During this time no messaging can be
performed.

The Broker has a background recovery feature allows the system to return
to operation sooner. If enabled the recovery process takes place in the
background allow producers and consumers to begin work earlier.

The feature respects the message delivery order requirements of standard
queues, that is any messages arriving whilst the background recovery is
in flight won't overtake older messages still to be recovered from disk.
There is an exception for the out of order queue types whilst background
recovery is in flight. For instance, with priority queues older lower
priority messages may be delivered before newer, higher priority.

To activate the feature, set a [context
variable](#Java-Broker-Management-Managing-Entities-General)
`use_async_message_store_recovery` at the desired Virtualhost, or at
Broker or higher to enable the feature broker-wide.

> **Note**
>
> The background recovery feature does not write operational log
> messages to indicate its progress. This means messages
> [MST-1004](#Java-Broker-Appendix-Operation-Logging-Message-MST-1004)
> and
> [MST-1005](#Java-Broker-Appendix-Operation-Logging-Message-MST-1005)
> will not be seen.
