# <span class="header-section-number">1</span> Document Scope And Intended Audience

The intended audience of this document is Java developers who are
familiar with the JMS specification. Readers are not required to know
all the details of AMQP protocols. However, some knowledge of AMQP basic
concepts would be advantageous for reading of this document.

This document only covers the usage of 0-8, 0-9 and 0-9-1 AMQP protocols
with Qpid JMS client. The specifications for these protocols are
available from the [AMQP web site](&amqpSrc;).

The document covers some specific implementation details of JMS
connections, sessions, consumers and producers in ?. It also
demonstrates how to write a simple point to point and simple
publish/subscribe application using Qpid JMS Client in ?.

The Qpid JMS Client supports various configuration options which can be
set via JVM system properties, connection URLs and JNDI configuration
file. The setting of system properties is described in ?. The details of
supported options within the connection URLs are given in ?. The details
of Qpid JMS client JNDI properties format is provided in ?. The Qpid
destination URL format is covered in ?.

The Qpid JMS Client can be used for writing of JMS vendor neutral
messaging applications. However, in some cases it might be required to
use specific AMQP features. Thus, the Qpid client provides the extended
operation set to invoke those features.

? provides the details about turning on client logging which can help in
debugging of various issues while developing the messaging applications.

The details about Qpid JMS Client Exceptions are provided in ?
