# <span class="header-section-number">1</span> Introduction

Qpid JMS client is an implementation of [JMS specification
1.1](&oracleJmsSpec;). It utilises an [AMQP](&amqpSrc;) transport layer
for the performing of messaging operations. The client is intended to be
used for the writing of JMS compatible messaging applications. Such
applications can send and receive messages via any AMQP-compatible
brokers like RabbitMQ, Qpid Java Broker which support the AMQP protocols
0-8, 0-9, or 0-9-1.

The Qpid JMS client hides the details of AMQP transport implementation
behind the JMS API. Thus, the developers need only to be familiar with
JMS API in order to use the client. However, the knowledge of the basic
concepts of AMQP protocols can help developers in writing reliable and
high-performant messaging application.

> **Important**
>
> This book documents the behaviour of the Qpid JMS client when used
> with the AMQP protocols *0-8, 0-9, and 0-9-1* only. For behaviour when
> using the client with AMQP 0-10 protocol, please refer to [Programming
> in Apache Qpid](&qpidProgrammingBook;).
