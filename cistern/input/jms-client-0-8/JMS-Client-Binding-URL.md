# <span class="header-section-number">1</span> Binding URL

The *Binding URL* syntax for addressing<span
id="fnref1">[^1^](#fn1)</span>. It allows the specification of the
bindings between a queue and an exchange, queue and exchange creation
arguments and some ancillary options.

The format for a *Binding URL* is provided below

    <Exchange Class>://<Exchange Name>/[<Destination>]/[<Queue>][?<option>='<value>'[&<option>='<value>']]
        

where

-   *Exchange Class*, specifies the type of the exchange, for example,
    *direct*,*topic*,*fanout*, etc.

-   *Exchange Name*, specifies the name of the exchange, for example,
    *amq.direct*,*amq.topic*, etc.

-   *Destination*, is an optional part of *Binding URL*. It can be used
    to specify a routing key with the non direct exchanges if an option
    *routingkey* is not specified. If both *Destination* and option
    *routingkey* are specified, then option *routingkey* has precedence.

-   *Queue*, is an optional part of *Binding URL* to specify a queue
    name for JMS queue destination. It is ignored in JMS topic
    destinations. Queue names may consist of any mixture of digits,
    letters, and underscores

-   *Options*, key-value pairs separated by '=' character specifying
    queue and exchange creation arguments, routing key, client
    behaviour, etc.

> **Important**
>
> Take care with the quoting surrounding option values. Each option
> value *must* be surrounded with single quotes (').

The following *Binding URL* options are currently defined:

<table>
<caption>Binding URL options</caption>
<colgroup>
<col width="33%" />
<col width="33%" />
<col width="33%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">Option</th>
<th align="left">Type</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left"><p>durable</p></td>
<td align="left"><p>boolean</p></td>
<td align="left"><p>Queue durability flag. If it is set to <em>true</em>, a durable queue is requested to create. The durable queue should be stored on the Broker and remained there after Broker restarts until it is explicitly deleted. This option has no meaning for JMS topic destinations, as by nature a topic destination only exists when a subscriber is connected. If durability is required for topic destinations, the durable subscription should be created.</p></td>
</tr>
<tr class="even">
<td align="left"><p>exclusive</p></td>
<td align="left"><p>boolean</p></td>
<td align="left"><p>Queue exclusivity flag. The client cannot use a queue that was declared as exclusive by another still-open connection.</p></td>
</tr>
<tr class="odd">
<td align="left"><p>autodelete</p></td>
<td align="left"><p>boolean</p></td>
<td align="left"><p>Queue auto-deletion flag. If it is set to <em>true</em> on queue creation, the queue is deleted if there are no remaining subscribers.</p></td>
</tr>
<tr class="even">
<td align="left"><p>exchangeautodelete</p></td>
<td align="left"><p>boolean</p></td>
<td align="left"><p>Exchange auto-deletion flag.</p></td>
</tr>
<tr class="odd">
<td align="left"><p>exchangedurable</p></td>
<td align="left"><p>boolean</p></td>
<td align="left"><p>Exchange durability flag. If it is set to <em>true</em> when creating a new exchange, the exchange will be marked as durable. Durable exchanges should remain active after Broker restarts. Non-durable exchanges are deleted on following Broker restart.</p></td>
</tr>
<tr class="even">
<td align="left"><p>routingkey</p></td>
<td align="left"><p>string</p></td>
<td align="left"><p>Defines the value of the binding key to bind a queue to the exchange. It is always required to specify for JMS topic destinations. If routing key option is not set in <em>Binding URL</em> and direct exchange class is specified, the queue name is used as a routing key. <em>MessagePublisher</em> uses routing key to publish messages onto exchange.</p></td>
</tr>
<tr class="odd">
<td align="left"><p>browse</p></td>
<td align="left"><p>boolean</p></td>
<td align="left"><p>If set to <em>true</em> on a destination for a message consumer, such consumer can only read messages on the queue but cannot consume them. The consumer behaves like a queue browser in this case.</p></td>
</tr>
<tr class="even">
<td align="left"><p>rejectbehaviour</p></td>
<td align="left"><p>string</p></td>
<td align="left"><p>Defines the reject behaviour for the re-delivered messages. If set to 'SERVER' the client delegates the requeue/DLQ decision to the server. If this option is not specified, the messages won't be moved to the DLQ (or dropped) when delivery count exceeds the maximum.</p></td>
</tr>
</tbody>
</table>

# <span class="header-section-number">2</span> Binding URL Examples

## <span class="header-section-number">2.1</span> Binding URLs for declaring of JMS Queues

The Qpid client Binding URLs for JMS queue destinations can be declared
using direct exchange (Mostly it is a pre-defined exchange with a name
"amq.direct". Also, custom direct exchanges can be used.):

    direct://amq.direct//<Queue Name>
             

The Binding URLs for destinations created with calls to
*Session.createQueue(String)* can be expressed as

    direct://amq.direct//<Queue Name>?durable='true'
             

The durability flag is set to *true* in such destinations.

    direct://amq.direct//myNonDurableQueue
    direct://amq.direct//myDurableQueue?durable='true'
    direct://amq.direct//myAnotherQueue?durable='true'&routingkey='myqueue'
    direct://amq.direct//myQueue?durable='true'&routingkey='myqueue'&rejectbehaviour='server'
    direct://custom.direct//yetAnotherQueue
            

## <span class="header-section-number">2.2</span> Binding URLs for declaring of JMS Topics

The Binding URLs for JMS queue destinations can be declared using topic
exchange (A pre-defined exchange having name "amq.topic" is used mainly.
However, custom topic exchanges can be used as well):

    topic://amq.topic//<Queue name>?routingkey='<Topic Name>'&exclusive='true'&autodelete='true'
             

The Binding URLs for a topic destination created with calls to
*Session.createTopic("hello")* is provided below:

    topic://amq.topic/hello/tmp_127_0_0_1_36973_1?routingkey='hello'&exclusive='true'&autodelete='true'
            

## <span class="header-section-number">2.3</span> Wildcard characters in routing keys for topic destinations

AMQP exchanges of class *topic* can route messages to the queues using
special matches containing wildcard characters (a "\#" matches one or
more words, a "\*" matches a single word). The routing keys words are
separated with a "." delimiter to distinguish words for matching. Thus,
if a consumer application specifies a routing key in the destination
like "usa.\#", it should receive all the messages matching to that
routing key. For example, "usa.boston", "usa.new-york", etc.

The examples of the *Binding URLs* having routing keys with wildcards
characters are provided below:

    topic://amq.topic?routingkey='stocks.#'
    topic://amq.topic?routingkey='stocks.*.ibm'
    topic://amq.topic?routingkey='stocks.nyse.ibm'
            

## <span class="header-section-number">2.4</span> More Examples

<table>
<caption>Binding URL examples</caption>
<colgroup>
<col width="50%" />
<col width="50%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">Binding URL</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left"><p>fanout://amq.fanout//myQueue</p></td>
<td align="left"><p>Binding URL binding queue &quot;myQueue&quot; to predefined &quot;amq.fanout&quot; exchange of class &quot;fanout&quot;</p></td>
</tr>
<tr class="even">
<td align="left"><p>topic://custom.topic//anotherQueue?routingkey='aq'</p></td>
<td align="left"><p>Binding URL binding queue &quot;anotherQueue&quot; to the exchange with name &quot;custom.topic&quot; of class &quot;topic&quot; using binding key &quot;aq&quot;.</p></td>
</tr>
</tbody>
</table>

------------------------------------------------------------------------

1.  <div id="fn1">

    </div>

    The client also supports the ADDR format. This is documented in
    [Programming in Apache Qpid](&qpidProgrammingBook;).[↩](#fnref1)


