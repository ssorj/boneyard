# <span class="header-section-number">1</span> Managing the C++ Broker

There are quite a few ways to interact with the C++ broker. The command
line tools include:

-   qpid-route - used to configure federation (a set of federated
    brokers)

-   qpid-config - used to configure queues, exchanges, bindings and list
    them etc

-   qpid-tool - used to view management information/statistics and call
    any management actions on the broker

-   qpid-printevents - used to receive and print QMF events

-   qpid-ha - used to interact with the High Availability module

## <span class="header-section-number">1.1</span> Using qpid-config

This utility can be used to create queues exchanges and bindings, both
durable and transient. Always check for latest options by running --help
command.

    $ qpid-config --help
    Usage:  qpid-config [OPTIONS]
            qpid-config [OPTIONS] exchanges [filter-string]
            qpid-config [OPTIONS] queues    [filter-string]
            qpid-config [OPTIONS] add exchange <type> <name> [AddExchangeOptions]
            qpid-config [OPTIONS] del exchange <name>
            qpid-config [OPTIONS] add queue <name> [AddQueueOptions]
            qpid-config [OPTIONS] del queue <name>
            qpid-config [OPTIONS] bind   <exchange-name> <queue-name> [binding-key]
            qpid-config [OPTIONS] unbind <exchange-name> <queue-name> [binding-key]

    Options:
        -b [ --bindings ]                         Show bindings in queue or exchange list
        -a [ --broker-addr ] Address (localhost)  Address of qpidd broker
             broker-addr is in the form:   [username/password@] hostname | ip-address [:<port>]
             ex:  localhost, 10.1.1.7:10000, broker-host:10000, guest/guest@localhost

    Add Queue Options:
        --durable            Queue is durable
        --file-count N (8)   Number of files in queue's persistence journal
        --file-size  N (24)  File size in pages (64Kib/page)
        --max-queue-size N   Maximum in-memory queue size as bytes
        --max-queue-count N  Maximum in-memory queue size as a number of messages
        --limit-policy [none | reject | flow-to-disk | ring | ring-strict]
                             Action taken when queue limit is reached:
                                 none (default) - Use broker's default policy
                                 reject         - Reject enqueued messages
                                 flow-to-disk   - Page messages to disk
                                 ring           - Replace oldest unacquired message with new
                                 ring-strict    - Replace oldest message, reject if oldest is acquired
        --order [fifo | lvq | lvq-no-browse]
                             Set queue ordering policy:
                                 fifo (default) - First in, first out
                                 lvq            - Last Value Queue ordering, allows queue browsing
                                 lvq-no-browse  - Last Value Queue ordering, browsing clients may lose data

    Add Exchange Options:
        --durable    Exchange is durable
        --sequence   Exchange will insert a 'qpid.msg_sequence' field in the message header
                     with a value that increments for each message forwarded.
        --ive        Exchange will behave as an 'initial-value-exchange', keeping a reference
                     to the last message forwarded and enqueuing that message to newly bound
                     queues.

Get the summary page

    $ qpid-config
    Total Exchanges: 6
              topic: 2
            headers: 1
             fanout: 1
             direct: 2
       Total Queues: 7
            durable: 0
        non-durable: 7

List the queues

    $ qpid-config queues
    Queue Name                                  Attributes
    =================================================================
    pub_start
    pub_done
    sub_ready
    sub_done
    perftest0                                   --durable
    reply-dhcp-100-18-254.bos.redhat.com.20713  auto-del excl
    topic-dhcp-100-18-254.bos.redhat.com.20713  auto-del excl

List the exchanges with bindings

    $ ./qpid-config -b exchanges
    Exchange '' (direct)
        bind pub_start => pub_start
        bind pub_done => pub_done
        bind sub_ready => sub_ready
        bind sub_done => sub_done
        bind perftest0 => perftest0
        bind mgmt-3206ff16-fb29-4a30-82ea-e76f50dd7d15 => mgmt-3206ff16-fb29-4a30-82ea-e76f50dd7d15
        bind repl-3206ff16-fb29-4a30-82ea-e76f50dd7d15 => repl-3206ff16-fb29-4a30-82ea-e76f50dd7d15
    Exchange 'amq.direct' (direct)
        bind repl-3206ff16-fb29-4a30-82ea-e76f50dd7d15 => repl-3206ff16-fb29-4a30-82ea-e76f50dd7d15
        bind repl-df06c7a6-4ce7-426a-9f66-da91a2a6a837 => repl-df06c7a6-4ce7-426a-9f66-da91a2a6a837
        bind repl-c55915c2-2fda-43ee-9410-b1c1cbb3e4ae => repl-c55915c2-2fda-43ee-9410-b1c1cbb3e4ae
    Exchange 'amq.topic' (topic)
    Exchange 'amq.fanout' (fanout)
    Exchange 'amq.match' (headers)
    Exchange 'qpid.management' (topic)
        bind mgmt.# => mgmt-3206ff16-fb29-4a30-82ea-e76f50dd7d15

## <span class="header-section-number">1.2</span> Using qpid-route

This utility is to create federated networks of brokers, This allows you
for forward messages between brokers in a network. Messages can be
routed statically (using "qpid-route route add") where the bindings that
control message forwarding are supplied in the route. Message routing
can also be dynamic (using "qpid-route dynamic add") where the messages
are automatically forwarded to clients based on their bindings to the
local broker.

    $ qpid-route
    Usage:  qpid-route [OPTIONS] dynamic add <dest-broker> <src-broker> <exchange> [tag] [exclude-list]
            qpid-route [OPTIONS] dynamic del <dest-broker> <src-broker> <exchange>

            qpid-route [OPTIONS] route add   <dest-broker> <src-broker> <exchange> <routing-key> [tag] [exclude-list]
            qpid-route [OPTIONS] route del   <dest-broker> <src-broker> <exchange> <routing-key>
            qpid-route [OPTIONS] queue add   <dest-broker> <src-broker> <exchange> <queue>
            qpid-route [OPTIONS] queue del   <dest-broker> <src-broker> <exchange> <queue>
            qpid-route [OPTIONS] route list  [<dest-broker>]
            qpid-route [OPTIONS] route flush [<dest-broker>]
            qpid-route [OPTIONS] route map   [<broker>]

            qpid-route [OPTIONS] link add  <dest-broker> <src-broker>
            qpid-route [OPTIONS] link del  <dest-broker> <src-broker>
            qpid-route [OPTIONS] link list [<dest-broker>]

    Options:
        -v [ --verbose ]         Verbose output
        -q [ --quiet ]           Quiet output, don't print duplicate warnings
        -d [ --durable ]         Added configuration shall be durable
        -e [ --del-empty-link ]  Delete link after deleting last route on the link
        -s [ --src-local ]       Make connection to source broker (push route)
        -t <transport> [ --transport <transport>]
                                 Specify transport to use for links, defaults to tcp

      dest-broker and src-broker are in the form:  [username/password@] hostname | ip-address [:<port>]
      ex:  localhost, 10.1.1.7:10000, broker-host:10000, guest/guest@localhost

A few examples:

    qpid-route dynamic add host1 host2 fed.topic
    qpid-route dynamic add host2 host1 fed.topic

    qpid-route -v route add host1 host2 hub1.topic hub2.topic.stock.buy
    qpid-route -v route add host1 host2 hub1.topic hub2.topic.stock.sell
    qpid-route -v route add host1 host2 hub1.topic 'hub2.topic.stock.#'
    qpid-route -v route add host1 host2 hub1.topic 'hub2.#'
    qpid-route -v route add host1 host2 hub1.topic 'hub2.topic.#'
    qpid-route -v route add host1 host2 hub1.topic 'hub2.global.#'

The link map feature can be used to display the entire federated network
configuration by supplying a single broker as an entry point:

    $ qpid-route route map localhost:10001

    Finding Linked Brokers:
        localhost:10001... Ok
        localhost:10002... Ok
        localhost:10003... Ok
        localhost:10004... Ok
        localhost:10005... Ok
        localhost:10006... Ok
        localhost:10007... Ok
        localhost:10008... Ok

    Dynamic Routes:

      Exchange fed.topic:
        localhost:10002 <=> localhost:10001
        localhost:10003 <=> localhost:10002
        localhost:10004 <=> localhost:10002
        localhost:10005 <=> localhost:10002
        localhost:10006 <=> localhost:10005
        localhost:10007 <=> localhost:10006
        localhost:10008 <=> localhost:10006

      Exchange fed.direct:
        localhost:10002  => localhost:10001
        localhost:10004  => localhost:10003
        localhost:10003  => localhost:10002
        localhost:10001  => localhost:10004

    Static Routes:

      localhost:10003(ex=amq.direct) <= localhost:10005(ex=amq.direct) key=rkey
      localhost:10003(ex=amq.direct) <= localhost:10005(ex=amq.direct) key=rkey2

## <span class="header-section-number">1.3</span> Using qpid-tool

This utility provided a telnet style interface to be able to view, list
all stats and action all the methods. Simple capture below. Best to just
play with it and mail the list if you have questions or want features
added.

    qpid:
    qpid: help
    Management Tool for QPID
    Commands:
        list                            - Print summary of existing objects by class
        list <className>                - Print list of objects of the specified class
        list <className> all            - Print contents of all objects of specified class
        list <className> active         - Print contents of all non-deleted objects of specified class
        list <list-of-IDs>              - Print contents of one or more objects (infer className)
        list <className> <list-of-IDs>  - Print contents of one or more objects
            list is space-separated, ranges may be specified (i.e. 1004-1010)
        call <ID> <methodName> <args> - Invoke a method on an object
        schema                          - Print summary of object classes seen on the target
        schema <className>              - Print details of an object class
        set time-format short           - Select short timestamp format (default)
        set time-format long            - Select long timestamp format
        quit or ^D                      - Exit the program
    qpid: list
    Management Object Types:
        ObjectType     Active  Deleted
        ================================
        qpid.binding   21      0
        qpid.broker    1       0
        qpid.client    1       0
        qpid.exchange  6       0
        qpid.queue     13      0
        qpid.session   4       0
        qpid.system    1       0
        qpid.vhost     1       0
    qpid: list qpid.system
    Objects of type qpid.system
        ID    Created   Destroyed  Index
        ==================================
        1000  21:00:02  -          host
    qpid: list 1000
    Object of type qpid.system: (last sample time: 21:26:02)
        Type    Element   1000
        =======================================================
        config  sysId     host
        config  osName    Linux
        config  nodeName  localhost.localdomain
        config  release   2.6.24.4-64.fc8
        config  version   #1 SMP Sat Mar 29 09:15:49 EDT 2008
        config  machine   x86_64
    qpid: schema queue
    Schema for class 'qpid.queue':
        Element                Type          Unit         Access      Notes   Description
        ===================================================================================================================
        vhostRef               reference                  ReadCreate  index
        name                   short-string               ReadCreate  index
        durable                boolean                    ReadCreate
        autoDelete             boolean                    ReadCreate
        exclusive              boolean                    ReadCreate
        arguments              field-table                ReadOnly            Arguments supplied in queue.declare
        storeRef               reference                  ReadOnly            Reference to persistent queue (if durable)
        msgTotalEnqueues       uint64        message                          Total messages enqueued
        msgTotalDequeues       uint64        message                          Total messages dequeued
        msgTxnEnqueues         uint64        message                          Transactional messages enqueued
        msgTxnDequeues         uint64        message                          Transactional messages dequeued
        msgPersistEnqueues     uint64        message                          Persistent messages enqueued
        msgPersistDequeues     uint64        message                          Persistent messages dequeued
        msgDepth               uint32        message                          Current size of queue in messages
        msgDepthHigh           uint32        message                          Current size of queue in messages (High)
        msgDepthLow            uint32        message                          Current size of queue in messages (Low)
        byteTotalEnqueues      uint64        octet                            Total messages enqueued
        byteTotalDequeues      uint64        octet                            Total messages dequeued
        byteTxnEnqueues        uint64        octet                            Transactional messages enqueued
        byteTxnDequeues        uint64        octet                            Transactional messages dequeued
        bytePersistEnqueues    uint64        octet                            Persistent messages enqueued
        bytePersistDequeues    uint64        octet                            Persistent messages dequeued
        byteDepth              uint32        octet                            Current size of queue in bytes
        byteDepthHigh          uint32        octet                            Current size of queue in bytes (High)
        byteDepthLow           uint32        octet                            Current size of queue in bytes (Low)
        enqueueTxnStarts       uint64        transaction                      Total enqueue transactions started
        enqueueTxnCommits      uint64        transaction                      Total enqueue transactions committed
        enqueueTxnRejects      uint64        transaction                      Total enqueue transactions rejected
        enqueueTxnCount        uint32        transaction                      Current pending enqueue transactions
        enqueueTxnCountHigh    uint32        transaction                      Current pending enqueue transactions (High)
        enqueueTxnCountLow     uint32        transaction                      Current pending enqueue transactions (Low)
        dequeueTxnStarts       uint64        transaction                      Total dequeue transactions started
        dequeueTxnCommits      uint64        transaction                      Total dequeue transactions committed
        dequeueTxnRejects      uint64        transaction                      Total dequeue transactions rejected
        dequeueTxnCount        uint32        transaction                      Current pending dequeue transactions
        dequeueTxnCountHigh    uint32        transaction                      Current pending dequeue transactions (High)
        dequeueTxnCountLow     uint32        transaction                      Current pending dequeue transactions (Low)
        consumers              uint32        consumer                         Current consumers on queue
        consumersHigh          uint32        consumer                         Current consumers on queue (High)
        consumersLow           uint32        consumer                         Current consumers on queue (Low)
        bindings               uint32        binding                          Current bindings
        bindingsHigh           uint32        binding                          Current bindings (High)
        bindingsLow            uint32        binding                          Current bindings (Low)
        unackedMessages        uint32        message                          Messages consumed but not yet acked
        unackedMessagesHigh    uint32        message                          Messages consumed but not yet acked (High)
        unackedMessagesLow     uint32        message                          Messages consumed but not yet acked (Low)
        messageLatencySamples  delta-time    nanosecond                       Broker latency through this queue (Samples)
        messageLatencyMin      delta-time    nanosecond                       Broker latency through this queue (Min)
        messageLatencyMax      delta-time    nanosecond                       Broker latency through this queue (Max)
        messageLatencyAverage  delta-time    nanosecond                       Broker latency through this queue (Average)
    Method 'purge' Discard all messages on queue
    qpid: list queue
    Objects of type qpid.queue
        ID    Created   Destroyed  Index
        ===========================================================================
        1012  21:08:13  -          1002.pub_start
        1014  21:08:13  -          1002.pub_done
        1016  21:08:13  -          1002.sub_ready
        1018  21:08:13  -          1002.sub_done
        1020  21:08:13  -          1002.perftest0
        1038  21:09:08  -          1002.mgmt-3206ff16-fb29-4a30-82ea-e76f50dd7d15
        1040  21:09:08  -          1002.repl-3206ff16-fb29-4a30-82ea-e76f50dd7d15
        1046  21:09:32  -          1002.mgmt-df06c7a6-4ce7-426a-9f66-da91a2a6a837
        1048  21:09:32  -          1002.repl-df06c7a6-4ce7-426a-9f66-da91a2a6a837
        1054  21:10:01  -          1002.mgmt-c55915c2-2fda-43ee-9410-b1c1cbb3e4ae
        1056  21:10:01  -          1002.repl-c55915c2-2fda-43ee-9410-b1c1cbb3e4ae
        1063  21:26:00  -          1002.mgmt-8d621997-6356-48c3-acab-76a37081d0f3
        1065  21:26:00  -          1002.repl-8d621997-6356-48c3-acab-76a37081d0f3
    qpid: list 1020
    Object of type qpid.queue: (last sample time: 21:26:02)
        Type    Element                1020
        ==========================================================================
        config  vhostRef               1002
        config  name                   perftest0
        config  durable                False
        config  autoDelete             False
        config  exclusive              False
        config  arguments              {'qpid.max_size': 0, 'qpid.max_count': 0}
        config  storeRef               NULL
        inst    msgTotalEnqueues       500000 messages
        inst    msgTotalDequeues       500000
        inst    msgTxnEnqueues         0
        inst    msgTxnDequeues         0
        inst    msgPersistEnqueues     0
        inst    msgPersistDequeues     0
        inst    msgDepth               0
        inst    msgDepthHigh           0
        inst    msgDepthLow            0
        inst    byteTotalEnqueues      512000000 octets
        inst    byteTotalDequeues      512000000
        inst    byteTxnEnqueues        0
        inst    byteTxnDequeues        0
        inst    bytePersistEnqueues    0
        inst    bytePersistDequeues    0
        inst    byteDepth              0
        inst    byteDepthHigh          0
        inst    byteDepthLow           0
        inst    enqueueTxnStarts       0 transactions
        inst    enqueueTxnCommits      0
        inst    enqueueTxnRejects      0
        inst    enqueueTxnCount        0
        inst    enqueueTxnCountHigh    0
        inst    enqueueTxnCountLow     0
        inst    dequeueTxnStarts       0
        inst    dequeueTxnCommits      0
        inst    dequeueTxnRejects      0
        inst    dequeueTxnCount        0
        inst    dequeueTxnCountHigh    0
        inst    dequeueTxnCountLow     0
        inst    consumers              0 consumers
        inst    consumersHigh          0
        inst    consumersLow           0
        inst    bindings               1 binding
        inst    bindingsHigh           1
        inst    bindingsLow            1
        inst    unackedMessages        0 messages
        inst    unackedMessagesHigh    0
        inst    unackedMessagesLow     0
        inst    messageLatencySamples  0
        inst    messageLatencyMin      0
        inst    messageLatencyMax      0
        inst    messageLatencyAverage  0
    qpid:

## <span class="header-section-number">1.4</span> Using qpid-printevents

This utility connects to one or more brokers and collects events,
printing out a line per event.

    $ qpid-printevents --help
    Usage: qpid-printevents [options] [broker-addr]...

    Collect and print events from one or more Qpid message brokers.  If no broker-
    addr is supplied, qpid-printevents will connect to 'localhost:5672'. broker-
    addr is of the form:  [username/password@] hostname | ip-address [:<port>] ex:
    localhost, 10.1.1.7:10000, broker-host:10000, guest/guest@localhost

    Options:
      -h, --help  show this help message and exit

You get the idea... have fun!

## <span class="header-section-number">1.5</span> Using qpid-ha

This utility lets you monitor and control the activity of the clustering
behavior provided by the HA module.

        
    qpid-ha --help
    usage: qpid-ha <command> [<arguments>]

    Commands are:

      ready        Test if a backup broker is ready.
      query        Print HA configuration settings.
      set          Set HA configuration settings.
      promote      Promote broker from backup to primary.
      replicate    Set up replication from <queue> on <remote-broker> to <queue> on the current broker.

    For help with a command type: qpid-ha <command> --help

      
