# <span class="header-section-number">1</span> Connection Limits

Each connection to the Broker consumes resources while it is connected.
In order to protect the Broker against malfunctioning (or malicious)
client processes, it is possible to limit the number of connections that
can be active on any given port.

Connection limits on AMQP ports are controlled by an attribute
"maxOpenConnections" on the port. By default this takes the value of the
context variable `qpid.port.max_open_connections` which in itself is
defaulted to the value `-1` meaning there is no limit.

If the interpolated value of `maxOpenConnections` on an AMQP port is a
positive integer, then when that many active connections have been
established no new connections will be allowed (until an existing
connection has been closed). Any such rejection of a connection will be
accompanied by the operational log message
[PRT-1005](#Java-Broker-Appendix-Operation-Logging-Message-PRT-1005).

The context variable `qpid.port.open_connections_warn_percent` can be
used to control when a warning log message is generated as the number of
open connections approaches the limit for the port. The default value of
this variable is `80` meaning that if more the number of open
connections to the port has exceeded 80% of the given limit then the
operatinal log message
[PRT-1004](#Java-Broker-Appendix-Operation-Logging-Message-PRT-1004)
will be generated.
