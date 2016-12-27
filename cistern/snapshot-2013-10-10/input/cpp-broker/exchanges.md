# Exchanges

[Up to Wiring](wiring.html)

XXX Yikes

## Configuring Exchange Options

The C++ Broker M4 or later supports the following additional Exchange
options in addition to the standard AMQP define options

-   Exchange Level Message sequencing

-   Initial Value Exchange

Note that these features can be used on any exchange type, that has been
declared with the options set.

It also supports an additional option to the bind operation on a direct
exchange

-   Exclusive binding for key

### Exchange Level Message sequencing

This feature can be used to place a sequence number into each message's
headers, based on the order they pass through an exchange. The
sequencing starts at 0 and then wraps in an AMQP int64 type.

The field name used is "qpid.msg\_sequence"

To use this feature an exchange needs to be declared specifying this
option in the declare

    ....
        FieldTable args;
        args.setInt("qpid.msg_sequence",1);

    ...
        // now declare the exchange
        session.exchangeDeclare(arg::exchange="direct", arg::arguments=args);

Then each message passing through that exchange will be numbers in the
application headers.

        unit64_t seqNo;
        //after message transfer
        seqNo = message.getHeaders().getAsInt64("qpid.msg_sequence");

### Initial Value Exchange

This feature caches a last message sent to an exchange. When a new
binding is created onto the exchange it will then attempt to route this
cached messaged to the queue, based on the binding. This allows for
topics or the creation of configurations where a new consumer can
receive the last message sent to the broker, with matching routing.

To use this feature an exchange needs to be declared specifying this
option in the declare

    ....
        FieldTable args;
        args.setInt("qpid.ive",1);

    ...
        // now declare the exchange
        session.exchangeDeclare(arg::exchange="direct", arg::arguments=args);

now use the exchange in the same way you would use any other exchange.

### Exclusive binding for key

Direct exchanges in qpidd support a qpid.exclusive-binding option on the
bind operation that causes the binding specified to be the only one for
the given key. I.e. if there is already a binding at this exchange with
this key it will be atomically updated to bind the new queue. This means
that the binding can be changed concurrently with an incoming stream of
messages and each message will be routed to exactly one queue.

    ....
        FieldTable args;
        args.setInt("qpid.exclusive-binding",1);

        //the following will cause the only binding from amq.direct with 'my-key' 
        //to be the one to 'my-queue'; if there were any previous bindings for that
        //key they will be removed. This is atomic w.r.t message routing through the
        //exchange.
        session.exchangeBind(arg::exchange="amq.direct", arg::queue="my-queue",
                             arg::bindingKey="my-key", arg::arguments=args);

    ...
