# Quotas

The ACL module enforces various quotas and thereby limits user activity.

## Connection limits

The ACL module creates broker command line switches that set limits on
the number of concurrent connections allowed per user or per client host
address. These settings are not specified in the ACL file.

        --max-connections           N
        --connection-limit-per-user N
        --connection-limit-per-ip   N
                

`--max-connections` specifies an upper limit for all user connections.

`--connection-limit-per-user` specifies an upper limit for each user
based on the authenticated user name. This limit is enforced regardless
of the client IP address from which the connection originates.

`--connection-limit-per-ip` specifies an upper limit for connections for
all users based on the originating client IP address. This limit is
enforced regardless of the user credentials presented with the
connection.

-   Note that addresses using different transports are counted
    separately even though the originating host is actually the same
    physical machine. In the setting illustrated above a host would
    allow N\_IP connections from [::1] IPv6 transport localhost and
    another N\_IP connections from [127.0.0.1] IPv4 transport localhost.
-   The connection-limit-per-ip and connection-limit-per-user counts are
    active simultaneously. From a given client system users may be
    denied access to the broker by either connection limit.

The 0.22 C++ Broker ACL module accepts fine grained per-user connection
limits through quota rules in the ACL file.

        quota connections 10 admins userX@QPID
                

-   User
    all
    receives the value passed by the command line switch
    --connection-limit-per-user
    .
-   Values specified in the ACL rule for user
    all
    overwrite the value specified on the command line if any.
-   Connection quotas values are determined by first searching for the
    authenticated user name. If that user name is not specified then the
    value for user
    all
    is used. If user
    all
    is not specified then the connection is denied.
-   The connection quota values range from 0..65530 inclusive. A value
    of zero disables connections from that user.
-   A user's quota may be specified many times in the ACL rule file.
    Only the last value specified is retained and enforced.
-   Per-user connection quotas are disabled when two conditions are
    true: 1) No --connection-limit-per-user command line switch and 2)
    No
    quota connections
    rules in the ACL file. Per-user connections are always counted even
    if connection quotas are not enforced. This supports ACL file
    reloading that may subsequently enable per-user connection quotas.
-   An ACL file reload may lower a user's connection quota value to a
    number lower than the user's current connection count. In that case
    the active connections remain unaffected. New connections are denied
    until that user closes enough of his connections so that his count
    falls below the configured limit.

### Queue Limits

The ACL module creates a broker command line switch that set limits on
the number of queues each user is allowed to create. This settings is
not specified in the ACL file.

        --max-queues-per-user N
                

The queue limit is set for all users on the broker.

The 0.22 C++ Broker ACL module accepts fine grained per-user queue
limits through quota rules in the ACL file.

        quota queues 10 admins userX@QPID
                

-   User
    all
    receives the value passed by the command line switch
    --max-queues-per-user
    .
-   Values specified in the ACL rule for user
    all
    overwrite the value specified on the command line if any.
-   Queue quotas values are determined by first searching for the
    authenticated user name. If that user name is not specified then the
    value for user
    all
    is used. If user
    all
    is not specified then the queue creation is denied.
-   The queue quota values range from 0..65530 inclusive. A value of
    zero disables queue creation by that user.
-   A user's quota may be specified many times in the ACL rule file.
    Only the last value specified is retained and enforced.
-   Per-user queue quotas are disabled when two conditions are true: 1)
    No --queue-limit-per-user command line switch and 2) No
    quota queues
    rules in the ACL file. Per-user queue creations are always counted
    even if queue quotas are not enforced. This supports ACL file
    reloading that may subsequently enable per-user queue quotas.
-   An ACL file reload may lower a user's queue quota value to a number
    lower than the user's current queue count. In that case the active
    queues remain unaffected. New queues are denied until that user
    closes enough of his queues so that his count falls below the
    configured limit.
