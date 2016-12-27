# <span class="header-section-number">1</span> AMQP compatibility

Qpid provides the most complete and compatible implementation of AMQP.
And is the most aggressive in implementing the latest version of the
specification.

There are two brokers:

-   C++ with support for AMQP 0-10

-   Java with support for AMQP 0-8 and 0-9 (0-10 planned)

There are client libraries for C++, Java (JMS), .Net (written in C\#),
python and ruby.

-   All clients support 0-10 and interoperate with the C++ broker.

<!-- -->

-   The JMS client supports 0-8, 0-9 and 0-10 and interoperates with
    both brokers.

<!-- -->

-   The python and ruby clients will also support all versions, but the
    API is dynamically driven by the specification used and so differs
    between versions. To work with the Java broker you must use 0-8 or
    0-9, to work with the C++ broker you must use 0-10.

<!-- -->

-   There are two separate C\# clients, one for 0-8 that interoperates
    with the Java broker, one for 0-10 that inteoperates with the C++
    broker.

QMF Management is supported in Ruby, Python, C++, and via QMan for Java
JMX & WS-DM.

## <span class="header-section-number">1.1</span> AMQP Compatibility of Qpid releases:

Qpid implements the AMQP Specification, and as the specification has
progressed Qpid is keeping up with the updates. This means that
different Qpid versions support different versions of AMQP. Here is a
simple guide on what use.

Here is a matrix that describes the different versions supported by each
release. The status symbols are interpreted as follows:

Y  
supported

N  
unsupported

IP  
in progress

P  
planned

|-------------------|------|------|-----|-----|-----|
| Component         | Spec |      |     |     |     |
|                   |      | M2.1 | M3  | M4  | 0.5 |
| java client       | 0-10 |      | Y   | Y   | Y   |
|                   | 0-9  | Y    | Y   | Y   | Y   |
|                   | 0-8  | Y    | Y   | Y   | Y   |
| java broker       | 0-10 |      |     |     | P   |
|                   | 0-9  | Y    | Y   | Y   | Y   |
|                   | 0-8  | Y    | Y   | Y   | Y   |
| c++ client/broker | 0-10 |      | Y   | Y   | Y   |
|                   | 0-9  | Y    |     |     |     |
| python client     | 0-10 |      | Y   | Y   | Y   |
|                   | 0-9  | Y    | Y   | Y   | Y   |
|                   | 0-8  | Y    | Y   | Y   | Y   |
| ruby client       | 0-10 |      |     | Y   | Y   |
|                   | 0-8  | Y    | Y   | Y   | Y   |
| C\# client        | 0-10 |      |     | Y   | Y   |
|                   | 0-8  | Y    | Y   | Y   | Y   |

## <span class="header-section-number">1.2</span> Interop table by AMQP specification version

Above table represented in another format.

|-------------------|-----------|-----|-----|------|
|                   | release   | 0-8 | 0-9 | 0-10 |
| java client       | M3 M4 0.5 | Y   | Y   | Y    |
| java client       | M2.1      | Y   | Y   | N    |
| java broker       | M3 M4 0.5 | Y   | Y   | N    |
| java broker       | trunk     | Y   | Y   | P    |
| java broker       | M2.1      | Y   | Y   | N    |
| c++ client/broker | M3 M4 0.5 | N   | N   | Y    |
| c++ client/broker | M2.1      | N   | Y   | N    |
| python client     | M3 M4 0.5 | Y   | Y   | Y    |
| python client     | M2.1      | Y   | Y   | N    |
| ruby client       | M3 M4 0.5 | Y   | Y   | N    |
| ruby client       | trunk     | Y   | Y   | P    |
| C\# client        | M3 M4 0.5 | Y   | N   | N    |
| C\# client        | trunk     | Y   | N   | Y    |


