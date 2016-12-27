# <span class="header-section-number">1</span> Log Files

The Broker uses the [Apache Log4J](http://logging.apache.org/log4j/1.2/)
Logging Framework for all logging activity.

In the Broker's shipped configuration, all logging is directed to log
file `${QPID_WORK}/log/qpid.log`. The log file is not rotated and will
be overwritten when the Broker restarts. Logging levels are configured
in such a way that the log will comprise of:

-   Opertional Log Events. These report key events in the lifecycle of
    objects (Broker start-up, Queue creation, Queue deletion etc) within
    the Broker. See ? for details of the formation of these messages.

-   Queue Alert Events. These report when the queue thresholds have been
    breached. See ? for details.

-   Any Error and Warning conditions.

Logging can be reconfigured either by changing the logging configuration
file `${QPID_HOME}/etc/log4j.xml` or at runtime using the Logging
Management MBean, see ? for details.

## <span class="header-section-number">1.1</span> Enabling Debug

It can be helpful to enable debug within the Broker in order to
understand a problem more clearly. If this is required, debug can be
enabled at runtime (without restarting the Broker) using the Logging
Management MBean. The change can also be made by changing the log
configuration file and restarting the Broker. Whichever mechanism is
chosen, change the appender associated with `org.apache.qpid` from
`WARN` to `DEBUG`.

    ...
    <logger additivity="true" name="org.apache.qpid">
        <level value="debug"/> <!-- change the level value from warn to debug -->
    </logger>
    ...

> **Important**
>
> Running a production system at `DEBUG` level can have performance
> implications by slowing the Broker down. It can also generate large
> log files. Take care to revert the logging level back to `WARN` after
> the analysis is performed.
