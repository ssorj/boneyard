# <span class="header-section-number">1</span> Management Channels

The Broker can be managed over a number of different channels.

-   HTTP - The primary channel for management. The HTTP interface
    comprises of a Web Console and a REST API.

-   JMX - The Broker provides a JMX compliant management interface. This
    is not currently undergoing further development and is retained
    largely for backward compatibility. It is suggested the new users
    favour the Web Console/REST API.

-   AMQP - The AMQP protocols 0-8..0-10 allow for some management of
    Exchanges, Queue and Bindings. This will be superseded by AMQP 1.0
    Management. It is suggested that new users favour the Management
    facilities provided by the Web Console/REST API.


