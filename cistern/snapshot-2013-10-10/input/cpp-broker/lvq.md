# Last Value Queue

A last value queue (LVQ) holds only one message for a particular key.

An LVQ is configured with the name of a message header that is used as
the key. The queue behaves as a normal FIFO queue with the exception
that when a message is enqueued, any other message in the queue with
the same value in the key header is removed and discarded.  Thus, for
any given key value, the queue holds only the most recent message.

The following example illustrates the operation of a last value queue.
The example shows an empty queue with no consumers and a sequence of
produced messages. The numbers represent the key for each message.

               <empty queue>
          1 =>
               1
          2 =>
               1 2
          3 =>
               1 2 3
          4 =>
               1 2 3 4
          2 =>
               1 3 4 2
          1 =>
               3 4 2 1

Note that the first four messages are enqueued normally in FIFO order.
The fifth message has key '2' and is also enqueued on the tail of the
queue. However, the message already in the queue with the same key is
discarded.

> **Note**
>
> If the set of keys used in the messages in an LVQ is constrained, the
> number of messages in the queue shall not exceed the number of
> distinct keys in use.

## Common use cases

 - *LVQ with zero or one consuming subscriptions* - In this case, if
   the consumer drops momentarily or is slower than the producer(s),
   it will only receive current information relative to the message
   keys.

 - *LVQ with zero or more browsing subscriptions* - A browsing
   consumer can subscribe to the LVQ and get an immediate dump of all
   of the "current" messages and track updates thereafter. Any number
   of independent browsers can subscribe to the same LVQ with the same
   effect. Since messages are never consumed, they only disappear when
   replaced with a newer message with the same key or when their TTL
   expires.

## Creating a last value queue

### Using address syntax

An LVQ may be created using directives in the Qpid Messaging API's
address syntax. The important argument is
`qpid.last\_value\_queue\_key`. The following Python example shows how
a producer of stock price updates can create an LVQ to hold the latest
stock prices for each ticker symbol. The message header used to hold
the ticker symbol is called "ticker".

    conn = Connection(url)
    conn.open()
    sess = conn.session()
    tx = sess.sender("prices;{create:always, node:{type:queue, x-declare:{arguments:{'qpid.last_value_queue_key':'ticker'}}}}")

### Using `qpid-config`

The same LVQ as shown in the previous example can be created using the
qpid-config utility:

    $ qpid-config add queue prices --lvq-key ticker

## Examples

### Sender

    from qpid.messaging import Connection, Message

    def send(sender, key, message):
        message.properties["ticker"] = key
        sender.send(message)

    conn = Connection("localhost")
    conn.open()
    sess = conn.session()
    tx = sess.sender("prices;{create:always, node:{type:queue,x-declare:{arguments:{'qpid.last_value_queue_key':ticker}}}}")

    msg = Message("Content")
    send(tx, "key1", msg);
    send(tx, "key2", msg);
    send(tx, "key3", msg);
    send(tx, "key4", msg);
    send(tx, "key2", msg);
    send(tx, "key1", msg);

    conn.close()

### Browsing receiver

    from qpid.messaging import Connection, Message

    conn = Connection("localhost")
    conn.open()
    sess = conn.session()
    rx = sess.receiver("prices;{mode:browse}")

    while True:
        msg = rx.fetch()
        sess.acknowledge()
        print msg

## Deprecated LVQ modes

XXX update?

There are two legacy modes (still implemented as of Qpid 0.14)
controlled by the qpid.last\_value\_queue and
qpid.last\_value\_queue\_no\_browse argument values. These modes are
deprecated and should not be used.
