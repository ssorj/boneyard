# Apache Qpid C++ Broker

 - [Overview](overview.html)
 - [Configuration](configuration.html)
    - [Logging](logging.html)
 - [Security](security.html)
    - [Authentication](authentication.html)
    - [Authorization](authorization.html)
        - [ACL syntax](acl-syntax.html)
    - [Quotas](quotas.html)
    - [SSL](ssl.html)
 - [Wiring](wiring.html)
    - [Exchanges](exchanges.html)
    - [Queues](queues.html)
        - [Last value queue](lvq.html)
        - [Producer flow control](producer-flow-control.html)
        - [Message groups](message-groups.html)
 - [Management](management.html)
 - [High availability](ha.html)
 - [Queue replication](queue-replication.html)
 - [Federation](federation.html)

## What I've changed

 - Simplified and regularized file names
 - Removed QMF content
 - Added a (currently empty) overview
 - Removed queue state replication (and kept the new HA queue replication)
 - Reorganized the configuration section
 - Added wiring page

## What's missing

 - Persistence
 - Heartbeats
 - Header-based routing (under exchanges)
 - Message TTLs
 - Resource limits (under security?)
 - Server-side selectors
 - Priority queue, ring queue
 - Threshold alerts (with resource limits?)
 - Transactions
 - Undeliverable message handling
 - Logging
 - Configuration

## Todo

 - Break security into smaller parts
 - Add navigation to pages
 - Split logging out
