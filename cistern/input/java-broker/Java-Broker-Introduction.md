# <span class="header-section-number">1</span> Introduction

The Java Broker is a powerful open-source message broker that implements
all versions of the [Advanced Message Queuing Protocol
(AMQP)](http://www.amqp.org). The Java Broker is actually one of two
message brokers provided by the [Apache Qpid
project](http://qpid.apache.org): the Java Broker and the C++ Broker.

This document relates to the Java Broker. The [C++ Broker is described
separately](&qpidCppBook;).

*Headline features*

-   100% Java implementation - runs on any platform supporting Java 1.7
    or higher

-   Messaging clients support in Java, C++, Python.

-   JMS 1.1 compliance (Java client).

-   Persistent and non-persistent (transient) message support

-   Supports for all common messaging patterns (point-to-point,
    publish/subscribe, fan-out etc).

-   Transaction support including XA<span id="fnref1">[^1^](#fn1)</span>

-   Supports for all versions of the AMQP protocol

-   Automatic message translation, allowing clients using different AMQP
    versions to communicate with each other.

-   Pluggable authentication architecture with out-of-the-box support
    for Kerberos, LDAP, External, and file-based authentication
    mechanisms.

-   Pluggable storage architecture with implementations including
    [Apache Derby](http://db.apache.org/derby/), [Oracle BDB
    JE](&oracleBdbProductOverviewUrl;)<span
    id="fnref2">[^2^](#fn2)</span>, and External Database

-   Web based management interface and programmatic management
    interfaces via REST and JMX APIs.

-   SSL support

-   High availability (HA) support.<span id="fnref3">[^3^](#fn3)</span>

------------------------------------------------------------------------

1.  <div id="fn1">

    </div>

    XA provided when using AMQP 0-10[↩](#fnref1)

2.  <div id="fn2">

    </div>

    Oracle BDB JE must be downloaded separately.[↩](#fnref2)

3.  <div id="fn3">

    </div>

    HA currently only available to users of the optional BDB JE HA based
    message store.[↩](#fnref3)


