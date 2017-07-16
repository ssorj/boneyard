# Morty

An example AMQP service using Node.js.

    [Start an AMQP server with SASL anonymous access enabled]

    $ sudo make install
    [...]

    $ morty //127.0.0.1:5672/morty
    morty: Created receiver for source address 'morty'

    $ qcall //127.0.0.1:5672/morty abc
    qcall: Created sender for target address 'morty'
    qcall: Created dynamic receiver for responses
    qcall: Sent request 'abc'
    qcall: Received response 'ABC'

`qcall` is from the qtools repo at https://github.com/ssorj/qtools.
