# <span class="header-section-number">1</span> Using Message Groups

This section describes how messaging applications can use the Message
Group feature provided by the Broker.

> **Note**
>
> The content of this section assumes the reader is familiar with the
> Message Group feature as described in the AMQP Messaging Broker user's
> guide. Please read the message grouping section in the Broker user's
> guide before using the examples given in this section.

## <span class="header-section-number">1.1</span> Creating Message Group Queues

The following examples show how to create a message group queue that
enforces ordered group consumption across multiple consumers.

    sender = connection.session().sender("msg-group-q;" +
                                         " {create:always, delete:receiver," +
                                         " node: {x-declare: {arguments:" +
                                         " {'qpid.group_header_key':'THE-GROUP'," +
                                         " 'qpid.shared_msg_group':1}}}}")
          

    std::string addr("msg-group-q; "
                     " {create:always, delete:receiver,"
                     " node: {x-declare: {arguments:"
                     " {qpid.group_header_key:'THE-GROUP',"
                     " qpid.shared_msg_group:1}}}}");
    Sender sender = session.createSender(addr);
          

    Session s = c.createSession(false, Session.CLIENT_ACKNOWLEDGE);
    String addr = "msg-group-q; {create:always, delete:receiver," +
                                 " node: {x-declare: {arguments:" +
                                 " {'qpid.group_header_key':'THE-GROUP'," +
                                 " 'qpid.shared_msg_group':1}}}}";
    Destination d = (Destination) new AMQAnyDestination(addr);
    MessageProducer sender = s.createProducer(d);
          

The example code uses the x-declare map to specify the message group
configuration that should be used for the queue. See the AMQP Messaging
Broker user's guide for a detailed description of these arguments. Note
that the qpid.group\_header\_key's value MUST be a string type if using
the C++ broker.

## <span class="header-section-number">1.2</span> Sending Grouped Messages

When sending grouped messages, the client must add a message property
containing the group identifier to the outgoing message. If using the
C++ broker, the group identifier must be a string type. The key used for
the property must exactly match the value passed in the
'qpid.group\_header\_key' configuration argument.

    group = "A"
    m = Message(content="some data", properties={"THE-GROUP": group})
    sender.send(m)

    group = "B"
    m = Message(content="some other group's data", properties={"THE-GROUP": group})
    sender.send(m)

    group = "A"
    m = Message(content="more data for group 'A'", properties={"THE-GROUP": group})
    sender.send(m)
          

    const std::string groupKey("THE-GROUP");
    {
        Message msg("some data");
        msg.getProperties()[groupKey] = std::string("A");
        sender.send(msg);
    }
    {
        Message msg("some other group's data");
        msg.getProperties()[groupKey] = std::string("B");
        sender.send(msg);
    }
    {
        Message msg("more data for group 'A'");
        msg.getProperties()[groupKey] = std::string("A");
        sender.send(msg);
    }
          

    String groupKey = "THE-GROUP";

    TextMessage tmsg1 = s.createTextMessage("some data");
    tmsg1.setStringProperty(groupKey, "A");
    sender.send(tmsg1);

    TextMessage tmsg2 = s.createTextMessage("some other group's data");
    tmsg2.setStringProperty(groupKey, "B");
    sender.send(tmsg2);

    TextMessage tmsg3 = s.createTextMessage("more data for group 'A'");
    tmsg3.setStringProperty(groupKey, "A");
    sender.send(tmsg3);
          

The examples above send two groups worth of messages to the queue
created in the previous example. Two messages belong to group "A", and
one belongs to group "B". Note that it is not necessary to complete
sending one group's messages before starting another. Also note that
there is no need to indicate to the broker when a new group is created
or an existing group retired - the broker tracks group state
automatically.

## <span class="header-section-number">1.3</span> Receiving Grouped Messages

Since the broker enforces group policy when delivering messages, no
special actions are necessary for receiving grouped messages from the
broker. However, applications must adhere to the rules for message group
consumption as described in the AMQP Messaging Broker user's guide.
