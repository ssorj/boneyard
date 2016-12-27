# <span class="header-section-number">1</span> Queue Alerts

The Broker supports a variety of queue alerting thresholds. Once
configured on a queue, these limits will be periodically written to the
log if these limits are breached, until the condition is rectified.

For example, if queue `myqueue` is configured with a message count alert
of 1000, and then owing to a failure of a downstream system messages
begin to accumulate on the queue, the following alerts will be written
periodically to the log.

    INFO [default:VirtualHostHouseKeepingTask] (queue.NotificationCheck) - MESSAGE_COUNT_ALERT
               On Queue myqueue - 1272: Maximum count on queue threshold (1000) breached.
      

Note that queue alerts are *soft* in nature; breaching the limit will
merely cause the alerts to be generated but messages will still be
accepted to the queue.

Queue Alerts

Alert Name

Alert Format and Purpose

MESSAGE\_COUNT\_ALERT

MESSAGE\_COUNT\_ALERT On Queue queuename - number of messages: Maximum
count on queue threshold (limit) breached.

The number of messages on the given queue has breached its configured
limit.

MESSAGE\_SIZE\_ALERT

MESSAGE\_SIZE\_ALERT On Queue queuename -message size : Maximum message
size threshold (limit) breached. [Message ID=message id]

The size of an individual messages has breached its configured limit.

QUEUE\_DEPTH\_ALERT

QUEUE\_DEPTH\_ALERT On Queue queuename - total size of all messages on
queue : Maximum queue depth threshold (limit) breached.

The total size of all messages on the queue has breached its configured
limit.

MESSAGE\_AGE\_ALERT

MESSAGE\_AGE\_ALERT On Queue queuename - age of message : Maximum age on
queue threshold (limit) breached.

The age of a message on the given queue has breached its configured
limit.
