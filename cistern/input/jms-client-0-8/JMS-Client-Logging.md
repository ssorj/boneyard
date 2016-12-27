# <span class="header-section-number">1</span> Logging

The Qpid JMS client uses the [Apache SLF4J](http://www.slf4j.org)
logging framework. All logging activity created by the client is
directed through the SLF4J API. SLF4J is a is a façade for other common
logging frameworks. This makes it easy for application authors to use
their prefered logging framework in their application stack, and have
the Qpid JMS Client use it too.

SLF4J suppplies bindings for many common logging frameworks
([JUL](&oracleJdkDocUrl;java/util/logging/package-summary.html), [Apache
Log4J](http://logging.apache.org/log4j/1.2/),
[Logback](http://logback.qos.ch).

Include the SLF4J binding corresponding to the logging framework of your
choosen logging framework on classpath. For full details, see the SLF4J
[documentation](http://www.slf4j.org).

# <span class="header-section-number">2</span> Recommended Production Logging Level

In production, it is recommended that you configure your logging
framework is configured with logger `org.apache.qpid` set to `WARN`.

If you are using Apache Log4j with a log4j.properties file, this simply
means adding the following line:

          org.apache.qpid=WARN
        

If you are using another logging framework, or you are using Log4j but
configuring in another manner, refer to the documentation accompanying
the logging framework for details of how to proceed.

# <span class="header-section-number">3</span> Enabling Debug

If you are experiencing a problem, it can be informative to enable debug
logging to allow the behaviour of the Qpid JMS client to be understood
at a deeper level.

To do this, set the `org.apache.qpid` logger to `DEBUG`.

If you are using Apache Log4j with a log4j.properties file, this simply
means adding (or changing) the following line:

          org.apache.qpid=DEBUG
        

If you are using another logging framework, or you are using Log4j but
configuring in another manner, refer to the documentation accompanying
the logging framework for details of how to proceed.
