# <span class="header-section-number">1</span> Security

This chapter describes how authentication, rule-based authorization,
encryption, and digital signing can be accomplished using Qpid.
Authentication is the process of verifying the identity of a user; in
Qpid, this is done using the SASL framework. Rule-based authorization is
a mechanism for specifying the actions that each user is allowed to
perform; in Qpid, this is done using an Access Control List (ACL) that
is part of the Qpid broker. Encryption is used to ensure that data is
not transferred in a plain-text format that could be intercepted and
read. Digital signatures provide proof that a given message was sent by
a known sender. Encryption and signing are done using SSL (they can also
be done using SASL, but SSL provides stronger encryption).

## <span class="header-section-number">1.1</span> User Authentication

AMQP uses Simple Authentication and Security Layer (SASL) to
authenticate client connections to the broker. SASL is a framework that
supports a variety of authentication methods. For secure applications,
we suggest `CRAM-MD5`, `DIGEST-MD5`, or `GSSAPI`. The `ANONYMOUS` method
is not secure. The `PLAIN` method is secure only when used together with
SSL.

Both the Qpid broker and Qpid clients use the [Cyrus SASL
library](http://cyrusimap.web.cmu.edu/), a full-featured authentication
framework, which offers many configuration options. This section shows
how to configure users for authentication with SASL, which is sufficient
when using `SASL PLAIN`. If you are not using SSL, you should configure
SASL to use `CRAM-MD5`, `DIGEST-MD5`, or `GSSAPI` (which provides
Kerberos authentication). For information on configuring these and other
options in SASL, see the Cyrus SASL documentation.

> **Important**
>
> The `SASL PLAIN` method sends passwords in cleartext, and is
> vulnerable to man-in-the-middle attacks unless SSL (Secure Socket
> Layer) is also used (see ?).
>
> If you are not using SSL, we recommend that you disable `PLAIN`
> authentication in the broker.

The Qpid broker uses the `auth yes|no` option to determine whether to
use SASL authentication. Turn on authentication by setting `auth` to
`yes` in `/etc/qpidd.conf`:

    # /etc/qpidd.conf
    #
    # Set auth to 'yes' or 'no'

    auth=yes

### <span class="header-section-number">1.1.1</span> Configuring SASL

On Linux systems, the SASL configuration file is generally found in
`/etc/sasl2/qpidd.conf` or `/usr/lib/sasl2/qpidd.conf`.

The SASL database contains user names and passwords for SASL. In SASL, a
user may be associated with a realm. The Qpid broker authenticates users
in the `QPID` realm by default, but it can be set to a different realm
using the `realm` option:

    # /etc/qpidd.conf
    #
    # Set the SASL realm using 'realm='

    auth=yes
    realm=QPID

The SASL database is installed at `/var/lib/qpidd/qpidd.sasldb`;
initially, it has one user named `guest` in the `QPID` realm, and the
password for this user is `guest`.

> **Note**
>
> The user database is readable only by the qpidd user. When run as a
> daemon, Qpid always runs as the qpidd user. If you start the broker
> from a user other than the qpidd user, you will need to either
> reconfigure SASL or turn authentication off.

> **Important**
>
> The SASL database stores user names and passwords in plain text. If it
> is compromised so are all of the passwords that it stores. This is the
> reason that the qpidd user is the only user that can read the
> database. If you modify permissions, be careful not to expose the SASL
> database.

Add new users to the database by using the `saslpasswd2` command, which
specifies a realm and a user ID. A user ID takes the form
`user-id@domain.`.

    # saslpasswd2 -f /var/lib/qpidd/qpidd.sasldb -u realm new_user_name

To list the users in the SASL database, use `sasldblistusers2`:

    # sasldblistusers2 -f /var/lib/qpidd/qpidd.sasldb

If you are using `PLAIN` authentication, users who are in the database
can now connect with their user name and password. This is secure only
if you are using SSL. If you are using a more secure form of
authentication, please consult your SASL documentation for information
on configuring the options you need.

### <span class="header-section-number">1.1.2</span> Kerberos

Both the Qpid broker and Qpid users are 'principals' of the Kerberos
server, which means that they are both clients of the Kerberos
authentication services.

To use Kerberos, both the Qpid broker and each Qpid user must be
authenticated on the Kerberos server:

Install the Kerberos workstation software and Cyrus SASL GSSAPI on each
machine that runs a qpidd broker or a qpidd messaging client:

    $ sudo yum install cyrus-sasl-gssapi krb5-workstation

Make sure that the Qpid broker is registered in the Kerberos database.

Traditionally, a Kerberos principal is divided into three parts: the
primary, the instance, and the realm. A typical Kerberos V5 has the
format `primary/instance@REALM`. For a Qpid broker, the primary is
`qpidd`, the instance is the fully qualified domain name, which you can
obtain using `hostname --fqdn`, and the REALM is the Kerberos domain
realm. By default, this realm is `QPID`, but a different realm can be
specified in qpid.conf, e.g.:

    realm=EXAMPLE.COM

For instance, if the fully qualified domain name is
`dublduck.example.com` and the Kerberos domain realm is `EXAMPLE.COM`,
then the principal name is `qpidd/dublduck.example.com@EXAMPLE.COM`.

The following script creates a principal for qpidd:

    FDQN=`hostname --fqdn`
    REALM="EXAMPLE.COM"
    kadmin -r $REALM  -q "addprinc -randkey -clearpolicy qpidd/$FQDN"

Now create a Kerberos keytab file for the Qpid broker. The Qpid broker
must have read access to the keytab file. The following script creates a
keytab file and allows the broker read access:

    QPIDD_GROUP="qpidd"
    kadmin -r $REALM  -q "ktadd -k /etc/qpidd.keytab qpidd/$FQDN@$REALM"
    chmod g+r /etc/qpidd.keytab
    chgrp $QPIDD_GROUP /etc/qpidd.keytab

The default location for the keytab file is `/etc/krb5.keytab`. If a
different keytab file is used, the KRB5\_KTNAME environment variable
must contain the name of the file, e.g.:

    export KRB5_KTNAME=/etc/qpidd.keytab

If this is correctly configured, you can now enable kerberos support on
the Qpid broker by setting the `auth` and `realm` options in
`/etc/qpidd.conf`:

    # /etc/qpidd.conf
    auth=yes
    realm=EXAMPLE.COM

Restart the broker to activate these settings.

Make sure that each Qpid user is registered in the Kerberos database,
and that Kerberos is correctly configured on the client machine. The
Qpid user is the account from which a Qpid messaging client is run. If
it is correctly configured, the following command should succeed:

    $ kinit user@REALM.COM

Java JMS clients require a few additional steps.

The Java JVM must be run with the following arguments:

-Djavax.security.auth.useSubjectCredsOnly=false  
Forces the SASL GASSPI client to obtain the kerberos credentials
explicitly instead of obtaining from the "subject" that owns the current
thread.

-Djava.security.auth.login.config=myjas.conf  
Specifies the jass configuration file. Here is a sample JASS
configuration file:

    com.sun.security.jgss.initiate {
        com.sun.security.auth.module.Krb5LoginModule required useTicketCache=true;
    };

-Dsun.security.krb5.debug=true  
Enables detailed debug info for troubleshooting

The client's Connection URL must specify the following Kerberos-specific
broker properties:

-   `sasl_mechs` must be set to `GSSAPI`.

-   `sasl_protocol` must be set to the principal for the qpidd broker,
    e.g. `qpidd`/

-   `sasl_server` must be set to the host for the SASL server, e.g.
    `sasl.com`.

Here is a sample connection URL for a Kerberos connection:

    amqp://guest@clientid/testpath?brokerlist='tcp://localhost:5672?sasl_mechs='GSSAPI'&sasl_protocol='qpidd'&sasl_server='<server-host-name>''

## <span class="header-section-number">1.2</span> Authorization

In Qpid, Authorization specifies which actions can be performed by each
authenticated user using an Access Control List (ACL).

Use the `--acl-file` command to load the access control list. The
filename should have a `.acl` extension:

        $ qpidd --acl-file ./aclfilename.acl

Each line in an ACL file grants or denies specific rights to a user. If
the last line in an ACL file is `acl deny all all`, the ACL uses deny
mode, and only those rights that are explicitly allowed are granted:

        acl allow rajith@QPID all all
        acl deny all all

On this server, `rajith@QPID` can perform any action, but nobody else
can. Deny mode is the default, so the previous example is equivalent to
the following ACL file:

        acl allow rajith@QPID all all

Alternatively the ACL file may use allow mode by placing:

        acl allow all all

as the final line in the ACL file. In *allow mode* all actions by all
users are allowed unless otherwise denied by specific ACL rules. The ACL
rule which selects *deny mode* or *allow mode* must be the last line in
the ACL rule file.

ACL syntax allows fine-grained access rights for specific actions:

        acl allow carlt@QPID create exchange name=carl.*
        acl allow fred@QPID create all
        acl allow all consume queue
        acl allow all bind exchange
        acl deny all all

An ACL file can define user groups, and assign permissions to them:

        group admin ted@QPID martin@QPID
        acl allow admin create all
        acl deny all all

An ACL file can define per user connection and queue quotas:

        group admin ted@QPID martin@QPID
        group blacklist usera@qpid userb@qpid
        quota connections 10 admin
        quota connections  5 all
        quota connections  0 blacklist
        quota queues      50 admin
        quota queues       5 all
        quota queues       1 test@qpid

Performance Note: Most ACL queries are performed infrequently. The
overhead associated with ACL passing an allow or deny decision on the
creation of a queue is negligible compared to actually creating and
using the queue. One notable exception is the `publish exchange` query.
ACL files with no *publish exchange* rules are noted and the broker
short circuits the logic associated with the per-messsage *publish
exchange* ACL query. However, if an ACL file has any *publish exchange*
rules then the broker is required to perform a *publish exchange* query
for each message published. Users with performance critical applications
are encouraged to structure exchanges, queues, and bindings so that the
*publish exchange* ACL rules are unnecessary.

### <span class="header-section-number">1.2.1</span> ACL Syntax

ACL rules follow this syntax:

    aclline = ( comment | aclspec | groupspec | quotaspec )

    comment = "#" [ STRING ]

    aclspec = "acl" permission ( groupname | name | "all" )
              ( action | "all" ) [ ( object | "all ) [ ( property "=" STRING )* ] ]

    groupspec = "group" groupname ( name )* [ "\" ]

    groupcontinuation = ( name )* [ "\" ]

    quotaspec = "quota" ( "connections" | "queues" ) NUMBER ( groupname | name | "all" )*

    name = ( ALPHANUMERIC | "-" | "_" | "." | "@" | "/" ) [ ( ALPHANUMERIC | "-" | "_" | "." | "@" | "/" )* ]

    groupname = ( ALPHANUMERIC | "-" | "_" ) [ ( ALPHANUMERIC | "-" | "_" )* ]

    permission = "allow" | "allow-log" | "deny" | "deny-log"

    action = "consume" | "publish" | "create" | "access" |
             "bind"    | "unbind"  | "delete" | "purge"  |
             "update"

    object = "queue"  | "exchange" | "broker"     | "link" |
             "method" | "query"    | "connection"

    property =  "name" | "durable" | "routingkey" | "autodelete" |
                "exclusive" | "type" | "alternate" | "queuename"  |
                "exchangename" | "schemapackage" | "schemaclass" |
                "policytype" | "paging" |
                "queuemaxsizelowerlimit"  | "queuemaxsizeupperlimit" |
                "queuemaxcountlowerlimit" | "queuemaxcountupperlimit" |
                "filemaxsizelowerlimit"   | "filemaxsizeupperlimit" |
                "filemaxcountlowerlimit"  | "filemaxcountupperlimit" |
                "pageslowerlimit"         | "pagesupperlimit" |
                "pagefactorlowerlimit"    | "pagefactorupperlimit"

ACL rules can also include a single object name (or the keyword `all`)
and one or more property name value pairs in the form `property=value`

The following tables show the possible values for `permission`,
`action`, `object`, and `property` in an ACL rules file.

<table>
<caption>ACL Rules: permission</caption>
<colgroup>
<col width="50%" />
<col width="50%" />
</colgroup>
<tbody>
<tr class="odd">
<td align="left"><code>allow</code></td>
<td align="left"><p>Allow the action</p></td>
</tr>
<tr class="even">
<td align="left"><code>allow-log</code></td>
<td align="left"><p>Allow the action and log the action in the event log</p></td>
</tr>
<tr class="odd">
<td align="left"><code>deny</code></td>
<td align="left"><p>Deny the action</p></td>
</tr>
<tr class="even">
<td align="left"><code>deny-log</code></td>
<td align="left"><p>Deny the action and log the action in the event log</p></td>
</tr>
</tbody>
</table>

<table>
<caption>ACL Rules: action</caption>
<colgroup>
<col width="50%" />
<col width="50%" />
</colgroup>
<tbody>
<tr class="odd">
<td align="left"><code>access</code></td>
<td align="left"><p>Accessing or reading an object</p></td>
</tr>
<tr class="even">
<td align="left"><code>bind</code></td>
<td align="left"><p>Associating a queue to an exchange with a routing key.</p></td>
</tr>
<tr class="odd">
<td align="left"><code>consume</code></td>
<td align="left"><p>Using an object</p></td>
</tr>
<tr class="even">
<td align="left"><code>create</code></td>
<td align="left"><p>Creating an object.</p></td>
</tr>
<tr class="odd">
<td align="left"><code>delete</code></td>
<td align="left"><p>Deleting an object.</p></td>
</tr>
<tr class="even">
<td align="left"><code>move</code></td>
<td align="left"><p>Moving messages between queues.</p></td>
</tr>
<tr class="odd">
<td align="left"><code>publish</code></td>
<td align="left"><p>Authenticating an incoming message.</p></td>
</tr>
<tr class="even">
<td align="left"><code>purge</code></td>
<td align="left"><p>Purging a queue.</p></td>
</tr>
<tr class="odd">
<td align="left"><code>redirect</code></td>
<td align="left"><p>Redirecting messages between queues</p></td>
</tr>
<tr class="even">
<td align="left"><code>reroute</code></td>
<td align="left"><p>Rerouting messages from a queue to an exchange</p></td>
</tr>
<tr class="odd">
<td align="left"><code>unbind</code></td>
<td align="left"><p>Disassociating a queue from an exchange with a routing key.</p></td>
</tr>
<tr class="even">
<td align="left"><code>update</code></td>
<td align="left"><p>Changing a broker configuration setting.</p></td>
</tr>
</tbody>
</table>

<table>
<caption>ACL Rules:object</caption>
<colgroup>
<col width="50%" />
<col width="50%" />
</colgroup>
<tbody>
<tr class="odd">
<td align="left"><code>broker</code></td>
<td align="left"></td>
</tr>
<tr class="even">
<td align="left"><code>connection</code></td>
<td align="left"><p>Incoming TCP/IP connection</p></td>
</tr>
<tr class="odd">
<td align="left"><code>exchange</code></td>
<td align="left"></td>
</tr>
<tr class="even">
<td align="left"><code>link</code></td>
<td align="left"><p>A federation or inter-broker link</p></td>
</tr>
<tr class="odd">
<td align="left"><code>method</code></td>
<td align="left"><p>Management method</p></td>
</tr>
<tr class="even">
<td align="left"><code>query</code></td>
<td align="left"><p>Management query of an object or class</p></td>
</tr>
<tr class="odd">
<td align="left"><code>queue</code></td>
<td align="left"></td>
</tr>
</tbody>
</table>

  ---------------------------------------------------------------------------
  Property           Type               Description        Usage
  ------------------ ------------------ ------------------ ------------------
  `name`             String             Rule refers to     
                                        objects with this  
                                        name. When 'name'  
                                        is blank or absent 
                                        then the rule      
                                        applies to all     
                                        objects of the     
                                        given type.        

  `alternate`        String             Name of an         CREATE QUEUE,
                                        alternate exchange CREATE EXCHANGE,
                                                           ACCESS QUEUE,
                                                           ACCESS EXCHANGE,
                                                           DELETE QUEUE,
                                                           DELETE EXCHANGE

  `autodelete`       Boolean            Indicates whether  CREATE QUEUE,
                                        or not the object  CREATE EXCHANGE,
                                        gets deleted when  ACCESS QUEUE,
                                        the connection     ACCESS EXCHANGE,
                                        that created it is DELETE QUEUE
                                        closed             

  `durable`          Boolean            Rule applies to    CREATE QUEUE,
                                        durable objects    CREATE EXCHANGE,
                                                           ACCESS QUEUE,
                                                           ACCESS EXCHANGE,
                                                           DELETE QUEUE,
                                                           DELETE EXCHANGE

  `exchangename`     String             Name of the        REROUTE QUEUE
                                        exchange to which  
                                        queue's entries    
                                        are routed         

  `filemaxcountlower Integer            Minimum value for  CREATE QUEUE
  limit`                                file.max\_count    
                                        (files)            

  `filemaxcountupper Integer            Maximum value for  CREATE QUEUE
  limit`                                file.max\_count    
                                        (files)            

  `filemaxsizelowerl Integer            Minimum value for  CREATE QUEUE
  imit`                                 file.max\_size     
                                        (64kb pages)       

  `filemaxsizeupperl Integer            Maximum value for  CREATE QUEUE
  imit`                                 file.max\_size     
                                        (64kb pages)       

  `host`             String             Target TCP/IP host CREATE CONNECTION
                                        or host range for  
                                        create connection  
                                        rules              

  `exclusive`        Boolean            Indicates the      CREATE QUEUE,
                                        presence of an     ACCESS QUEUE,
                                        `exclusive` flag   DELETE QUEUE

  `pagefactorlowerli Integer            Minimum value for  CREATE QUEUE
  mit`                                  size of a page in  
                                        paged queue        

  `pagefactorupperli Integer            Maximum value for  CREATE QUEUE
  mit`                                  size of a page in  
                                        paged queue        

  `pageslowerlimit`  Integer            Minimum value for  CREATE QUEUE
                                        number of paged    
                                        queue pages in     
                                        memory             

  `pagesupperlimit`  Integer            Maximum value for  CREATE QUEUE
                                        number of paged    
                                        queue pages in     
                                        memory             

  `paging`           Boolean            Indicates if the   CREATE QUEUE
                                        queue is a paging  
                                        queue              

  `policytype`       String             "ring",            CREATE QUEUE,
                                        "self-destruct",   ACCESS QUEUE,
                                        "reject"           DELETE QUEUE

  `queuename`        String             Name of the target ACCESS EXCHANGE,
                                        queue              BIND EXCHANGE,
                                                           MOVE QUEUE, UNBIND
                                                           EXCHANGE

  `queuemaxsizelower Integer            Minimum value for  CREATE QUEUE,
  limit`                                queue.max\_size    ACCESS QUEUE
                                        (memory bytes)     

  `queuemaxsizeupper Integer            Maximum value for  CREATE QUEUE,
  limit`                                queue.max\_size    ACCESS QUEUE
                                        (memory bytes)     

  `queuemaxcountlowe Integer            Minimum value for  CREATE QUEUE,
  rlimit`                               queue.max\_count   ACCESS QUEUE
                                        (messages)         

  `queuemaxcountuppe Integer            Maximum value for  CREATE QUEUE,
  rlimit`                               queue.max\_count   ACCESS QUEUE
                                        (messages)         

  `routingkey`       String             Specifies routing  BIND EXCHANGE,
                                        key                UNBIND EXCHANGE,
                                                           ACCESS EXCHANGE,
                                                           PUBLISH EXCHANGE

  `schemaclass`      String             QMF schema class   ACCESS METHOD,
                                        name               ACCESS QUERY

  `schemapackage`    String             QMF schema package ACCESS METHOD
                                        name               

  `type`             String             Type of exchange,  CREATE EXCHANGE,
                                        such as topic,     ACCESS EXCHANGE,
                                        fanout, or xml     DELETE EXCHANGE
  ---------------------------------------------------------------------------

#### <span class="header-section-number">1.2.1.1</span> ACL Action-Object-Property Combinations

Not every ACL action is applicable to every ACL object. Furthermore, not
every property may be specified for every action-object pair. The
following table lists the broker events that trigger ACL lookups. Then
for each event it lists the action, object, and properties allowed in
the lookup.

User-specified ACL rules constrain property sets to those that match one
or more of the action and object pairs. For example these rules are
allowed:

        acl allow all access exchange
        acl allow all access exchange name=abc
        acl allow all access exchange name=abc durable=true

These rules could possibly match one or more of the broker lookups.
However, this rule is not allowed:

        acl allow all access exchange queuename=queue1 durable=true

Properties *queuename* and *durable* are not in the list of allowed
properties for any 'access exchange' lookup. This rule would never match
a broker lookup query and would never contribute to an allow or deny
decision.

For more information about matching ACL rules please refer to [ACL Rule
Matching](#sect-Messaging_User_Guide-Authorization-ACL_Rule_Matching)

  ---------------------------------------------------------------------------
  Lookup Event       Action             Object             Properties
  ------------------ ------------------ ------------------ ------------------
  User querying      access             broker             
  message timestamp                                        
  setting                                                  

  AMQP 0-10 protocol access             exchange           name
  received 'query'                                         

  AMQP 0-10 query    access             exchange           name queuename
  binding                                                  routingkey

  AMQP 0-10 exchange access             exchange           name type
  declare                                                  alternate durable
                                                           autodelete

  AMQP 1.0 exchange  access             exchange           name type durable
  access                                                   

  AMQP 1.0 node      access             exchange           name
  resolution                                               

  Management method  access             method             name schemapackage
  request                                                  schemaclass

  Management agent   access             method             name schemapackage
  method request                                           schemaclass

  Management agent   access             query              name schemaclass
  query                                                    

  QMF 'query queue'  access             queue              name
  method                                                   

  AMQP 0-10 query    access             queue              name

  AMQP 0-10 queue    access             queue              name alternate
  declare                                                  durable exclusive
                                                           autodelete
                                                           policytype
                                                           queuemaxcountlower
                                                           limit
                                                           queuemaxcountupper
                                                           limit
                                                           queuemaxsizelowerl
                                                           imit
                                                           queuemaxsizeupperl
                                                           imit

  AMQP 1.0 queue     access             queue              name alternate
  access                                                   durable exclusive
                                                           autodelete
                                                           policytype
                                                           queuemaxcountlower
                                                           limit
                                                           queuemaxcountupper
                                                           limit
                                                           queuemaxsizelowerl
                                                           imit
                                                           queuemaxsizeupperl
                                                           imit

  AMQP 1.0 node      access             queue              name
  resolution                                               

  AMQP 0-10 or QMF   bind               exchange           name queuename
  bind request                                             routingkey

  AMQP 1.0 new       bind               exchange           name queuename
  outgoing link from                                       routingkey
  exchange                                                 

  AMQP 0-10          consume            queue              name
  subscribe request                                        

  AMQP 1.0 new       consume            queue              name
  outgoing link from                                       
  queue                                                    

  TCP/IP connection  create             connection         host
  creation                                                 

  Create exchange    create             exchange           name type
                                                           alternate durable
                                                           autodelete

  Interbroker link   create             link               
  creation                                                 

  Interbroker link   create             link               
  creation                                                 

  Create queue       create             queue              name alternate
                                                           durable exclusive
                                                           autodelete
                                                           policytype paging
                                                           pageslowerlimit
                                                           pagesupperlimit
                                                           pagefactorlowerlim
                                                           it
                                                           pagefactorupperlim
                                                           it
                                                           queuemaxcountlower
                                                           limit
                                                           queuemaxcountupper
                                                           limit
                                                           queuemaxsizelowerl
                                                           imit
                                                           queuemaxsizeupperl
                                                           imit
                                                           filemaxcountlowerl
                                                           imit
                                                           filemaxcountupperl
                                                           imit
                                                           filemaxsizelowerli
                                                           mit
                                                           filemaxsizeupperli
                                                           mit

  Delete exchange    delete             exchange           name type
                                                           alternate durable

  Delete queue       delete             queue              name alternate
                                                           durable exclusive
                                                           autodelete
                                                           policytype

  Management 'move   move               queue              name queuename
  queue' request                                           

  AMQP 0-10 received publish            exchange           name routingkey
  message processing                                       

  AMQP 1.0 establish publish            exchange           routingkey
  sender link to                                           
  queue                                                    

  AMQP 1.0 received  publish            exchange           name routingkey
  message processing                                       

  Management 'purge  purge              queue              name
  queue' request                                           

  Management 'purge  purge              queue              name
  queue' request                                           

  Management         redirect           queue              name queuename
  'redirect queue'                                         
  request                                                  

  Management         reroute            queue              name exchangename
  'reroute queue'                                          
  request                                                  

  Management 'unbind unbind             exchange           name queuename
  exchange' request                                        routingkey

  User modifying     update             broker             
  message timestamp                                        
  setting                                                  
  ---------------------------------------------------------------------------

### <span class="header-section-number">1.2.2</span> ACL Syntactic Conventions

#### <span class="header-section-number">1.2.2.1</span> Comments

-   A line starting with the `#` character is considered a comment and
    is ignored.

-   Embedded comments and trailing comments are not allowed. The `#` is
    commonly found in routing keys and other AMQP literals which occur
    naturally in ACL rule specifications.

#### <span class="header-section-number">1.2.2.2</span> White Space

-   Empty lines and lines that contain only whitespace (' ', '\\f',
    '\\n', '\\r', '\\t', '\\v') are ignored.

-   Additional whitespace between and after tokens is allowed.

-   Group and Acl definitions must start with `group` and `acl`
    respectively and with no preceding whitespace.

#### <span class="header-section-number">1.2.2.3</span> Character Set

-   ACL files use 7-bit ASCII characters only

-   Group names may contain only

    -   [a-z]
    -   [A-Z]
    -   [0-9]
    -   '-' hyphen
    -   '\_' underscore
-   Individual user names may contain only

    -   [a-z]
    -   [A-Z]
    -   [0-9]
    -   '-' hyphen
    -   '\_' underscore
    -   '.' period
    -   '@' ampersand
    -   '/' slash

#### <span class="header-section-number">1.2.2.4</span> Case Sensitivity

-   All tokens are case sensitive. `name1` is not the same as `Name1`
    and `create` is not the same as `CREATE`.

#### <span class="header-section-number">1.2.2.5</span> Line Continuation

-   Group lists can be extended to the following line by terminating the
    line with the `'\'` character. No other ACL file lines may be
    continued.

-   Group specification lines may be continued only after the group name
    or any of the user names included in the group. See example below.

-   Lines consisting solely of a `'\'` character are not permitted.

-   The `'\'` continuation character is recognized only if it is the
    last character in the line. Any characters after the `'\'` are not
    permitted.

<!-- -->

        #
        # Examples of extending group lists using a trailing '\' character
        #
        group group1 name1 name2 \
        name3 name4 \
        name5

        group group2 \
                     group1 \
                     name6
        #
        # The following are illegal:
        #
        # '\' must be after group name
        #
        group \
              group3 name7 name8
        #
        # No empty extension line
        #
        group group4 name9 \
                           \
                     name10

#### <span class="header-section-number">1.2.2.6</span> Line Length

-   ACL file lines are limited to 1024 characters.

#### <span class="header-section-number">1.2.2.7</span> ACL File Keywords

ACL reserves several words for convenience and for context sensitive
substitution.

##### <span class="header-section-number">1.2.2.7.1</span> The `all` Keyword

The keyword all is reserved. It may be used in ACL rules to match all
individuals and groups, all actions, or all objects.

-   acl allow all create queue
-   acl allow bob@QPID all queue
-   acl allow bob@QPID create all

##### <span class="header-section-number">1.2.2.7.2</span> User Name and Domain Name Keywords

In the C++ Broker 0.20 a simple set of user name and domain name
substitution variable keyword tokens is defined. This provides
administrators with an easy way to describe private or shared resources.

Symbol substitution is allowed in the ACL file anywhere that text is
supplied for a property value.

In the following table an authenticated user named bob.user@QPID.COM has
his substitution keywords expanded.

| Keyword         | Expansion            |
|-----------------|----------------------|
| `${userdomain}` | bob\_user\_QPID\_COM |
| `${user}`       | bob\_user            |
| `${domain}`     | QPID\_COM            |

-   The original user name has the period “.” and ampersand “@”
    characters translated into underscore “\_”. This allows substitution
    to work when the substitution keyword is used in a routingkey in the
    Acl file.
-   The Acl processing matches \${userdomain} before matching either
    \${user} or \${domain}. Rules that specify the combination
    \${user}\_\${domain} will never match.

<!-- -->

      # Example:
      #
      # Administrators can set up Acl rule files that allow every user to create a
      # private exchange, a private queue, and a private binding between them.
      # In this example the users are also allowed to create private backup exchanges,
      # queues and bindings. This effectively provides limits to user's exchange,
      # queue, and binding creation and guarantees that each user gets exclusive
      # access to these resources.
      #
      #
      # Create primary queue and exchange:
      #
      acl allow all create  queue    name=$\{user}-work alternate=$\{user}-work2
      acl deny  all create  queue    name=$\{user}-work alternate=*
      acl allow all create  queue    name=$\{user}-work
      acl allow all create  exchange name=$\{user}-work alternate=$\{user}-work2
      acl deny  all create  exchange name=$\{user}-work alternate=*
      acl allow all create  exchange name=$\{user}-work
      #
      # Create backup queue and exchange
      #
      acl deny  all create  queue    name=$\{user}-work2 alternate=*
      acl allow all create  queue    name=$\{user}-work2
      acl deny  all create  exchange name=$\{user}-work2 alternate=*
      acl allow all create  exchange name=$\{user}-work2
      #
      # Bind/unbind primary exchange
      #
      acl allow all bind   exchange name=$\{user}-work routingkey=$\{user} queuename=$\{user}-work
      acl allow all unbind exchange name=$\{user}-work routingkey=$\{user} queuename=$\{user}-work
      #
      # Bind/unbind backup exchange
      #
      acl allow all bind   exchange name=$\{user}-work2 routingkey=$\{user} queuename=$\{user}-work2
      acl allow all unbind exchange name=$\{user}-work2 routingkey=$\{user} queuename=$\{user}-work2
      #
      # Access primary exchange
      #
      acl allow all access exchange name=$\{user}-work routingkey=$\{user} queuename=$\{user}-work
      #
      # Access backup exchange
      #
      acl allow all access exchange name=$\{user}-work2 routingkey=$\{user} queuename=$\{user}-work2
      #
      # Publish primary exchange
      #
      acl allow all publish exchange name=$\{user}-work routingkey=$\{user}
      #
      # Publish backup exchange
      #
      acl allow all publish exchange name=$\{user}-work2 routingkey=$\{user}
      #
      # deny mode
      #
      acl deny all all

#### <span class="header-section-number">1.2.2.8</span> Wildcards

ACL privides two types of wildcard matching to provide flexibility in
writing rules.

##### <span class="header-section-number">1.2.2.8.1</span> Property Value Wildcard

Text specifying a property value may end with a single trailing `*`
character. This is a simple wildcard match indicating that strings which
match up to that point are matches for the ACL property rule. An ACL
rule such as

        acl allow bob@QPID create queue name=bob*

allow user bob@QPID to create queues named bob1, bob2, bobQueue3, and so
on.

##### <span class="header-section-number">1.2.2.8.2</span> Topic Routing Key Wildcard

In the C++ Broker 0.20 the logic governing the ACL Match has changed for
each ACL rule that contains a routingkey property. The routingkey
property is matched according to Topic Exchange match logic the broker
uses when it distributes messages published to a topic exchange.

Routing keys are hierarchical where each level is separated by a period:

-   weather.usa
-   weather.europe.germany
-   weather.europe.germany.berlin
-   company.engineering.repository

Within the routing key hierarchy two wildcard characters are defined.

-   \* matches one field
-   \# matches zero or more fields

Suppose an ACL rule file is:

        acl allow-log uHash1@COMPANY publish exchange name=X routingkey=a.#.b
        acl deny all all
                                  

When user uHash1@COMPANY attempts to publish to exchange X the ACL will
return these results:

| routingkey in publish to exchange X | result    |
|-------------------------------------|-----------|
| `a.b`                               | allow-log |
| `a.x.b`                             | allow-log |
| `a.x.y.zz.b`                        | allow-log |
| `a.b.`                              | deny      |
| `q.x.b`                             | deny      |

### <span class="header-section-number">1.2.3</span> ACL Rule Matching

The minimum matching criteria for ACL rules are:

-   An actor (individually named or group member)
-   An action
-   An object

If a rule does not match the minimum criteria then that rule does not
control the ACL allow or deny decision.

ACL rules optionally specify object names and property name=value pairs.
If an ACL rule specifies an object name or property values than all of
them must match to cause the rule to match.

The following illustration shows how ACL rules are processed to find
matching rules.

        # Example of rule matching
        #
        # Using this ACL file content:

        (1)  acl deny bob create exchange name=test durable=true passive=true
        (2)  acl deny bob create exchange name=myEx type=direct
        (3)  acl allow all all

        #
        # Lookup 1. id:bob action:create objectType:exchange name=test
        #           {durable=false passive=false type=direct alternate=}
        #
        # ACL Match Processing:
        #  1. Rule 1 passes minimum criteria with user bob, action create,
        #     and object exchange.
        #  2. Rule 1 matches name=test.
        #  3. Rule 1 does not match the rule's durable=true with the requested
        #     lookup of durable=false.
        #  4. Rule 1 does not control the decision and processing continues
        #     to Rule 2.
        #  5. Rule 2 passes minimum criteria with user bob, action create,
        #     and object exchange.
        #  6. Rule 2 does not match the rule's name=myEx with the requested
        #     lookup of name=test.
        #  7. Rule 2 does not control the decision and processing continues
        #     to Rule 3.
        #  8. Rule 3 matches everything and the decision is 'allow'.
        #
        # Lookup 2. id:bob action:create objectType:exchange name=myEx
        #           {durable=true passive=true type=direct alternate=}
        #
        # ACL Match Processing:
        #  1. Rule 1 passes minimum criteria with user bob, action create,
        #     and object exchange.
        #  2. Rule 1 does not match the rule's name=test with the requested
        #     lookup of name=myEx.
        #  3. Rule 1 does not control the decision and processing continues
        #     to Rule 2.
        #  4. Rule 2 passes minimum criteria with user bob, action create,
        #     and object exchange.
        #  5. Rule 2 matches name=myEx.
        #  6. Rule 2 matches the rule's type=direct with the requested
        #     lookup of type=direct.
        #  7. Rule 2 is the matching rule and the decision is 'deny'.
        #

Referring to [ACL Properties Allowed for each Action and Object
table](#tabl-Messaging_User_Guide-ACL_Syntax-ACL_ActionObject_properties)
observe that some Action/Object pairs have different sets of allowed
properties. For example different broker ACL lookups for *access
exchange* have different property subsets.

        [1] access exchange name
        [2] access exchange name type alternate durable autodelete
        [3] access exchange name queuename routingkey
        [4] access exchange name type durable

If an ACL rule specifies the *autodelete* property then it can possibly
match only the second case above. It can never match cases 1, 3, and 4
because the broker calls to ACL will not present the autodelete property
for matching. To get proper matching the ACL rule must have only the
properties of the intended lookup case.

        acl allow bob access exchange alternate=other    ! may match pattern 2 only
        acl allow bob access exchange queuename=other    ! may match pattern 3 only
        acl allow bob access exchange durable=true       ! may match patterns 2 and 4 only
        acl deny  bob access exchange                    ! may match all patterns

### <span class="header-section-number">1.2.4</span> Specifying ACL Permissions

Now that we have seen the ACL syntax, we will provide representative
examples and guidelines for ACL files.

Most ACL files begin by defining groups:

        group admin ted@QPID martin@QPID
        group user-consume martin@QPID ted@QPID
        group group2 kim@QPID user-consume rob@QPID
        group publisher group2 \
        tom@QPID andrew@QPID debbie@QPID

Rules in an ACL file grant or deny specific permissions to users or
groups:

        acl allow carlt@QPID create exchange name=carl.*
        acl allow rob@QPID create queue
        acl allow guest@QPID bind exchange name=amq.topic routingkey=stocks.rht.#
        acl allow user-consume create queue name=tmp.*

        acl allow publisher publish all durable=false
        acl allow publisher create queue name=RequestQueue
        acl allow consumer consume queue durable=true
        acl allow fred@QPID create all
        acl allow bob@QPID all queue
        acl allow admin all
        acl allow all consume queue
        acl allow all bind exchange
        acl deny all all

In the previous example, the last line, `acl deny all all`, denies all
authorizations that have not been specifically granted. This is the
default, but it is useful to include it explicitly on the last line for
the sake of clarity. If you want to grant all rights by default, you can
specify `acl allow all all` in the last line.

ACL allows specification of conflicting rules. Be sure to specify the
most specific rules first followed by more general rules. Here is an
example:

        group users alice@QPID bob@QPID charlie@QPID
        acl deny  charlie@QPID create queue
        acl allow users        create queue
        acl deny all all

In this example users alice and bob would be able to create queues due
to their membership in the users group. However, user charlie is denied
from creating a queue despite his membership in the users group because
a deny rule for him is stated before the allow rule for the users group.

Do not allow `guest` to access and log QMF management methods that could
cause security breaches:

        group allUsers guest@QPID
        ...
        acl deny-log allUsers create link
        acl deny-log allUsers access method name=connect
        acl deny-log allUsers access method name=echo
        acl allow all all

### <span class="header-section-number">1.2.5</span> Auditing ACL Settings

The 0.30 C++ Broker ACL module provides a comprehensive set of run-time
and debug logging checks. The following example ACL file is used to
illustrate working with the ACL module debugging features.

       group x a@QPID b@QPID b2@QPID b3@QPID
       acl allow all delete broker
       acl allow all create queue name=abc
       acl allow all create queue exchangename=xyz
       acl allow all create connection host=1.1.1.1
       acl allow all access exchange alternate=abc queuename=xyz
       acl allow all access exchange queuename=xyz
       acl allow all access exchange alternate=abc
       acl allow a@qpid all all exchangename=123
       acl allow b@qpid all all
       acl allow all all

When this file is loaded it will show the following (truncated,
formatted) Info-level log.

      notice ACL: Read file "/home/chug/acl/svn-acl.acl"
      warning ACL rule ignored: Broker never checks for rules with
                                action: 'delete' and object: 'broker'
      warning ACL rule ignored: Broker checks for rules with
                                action: 'create' and object: 'queue'
                  but will never match with property set: { exchangename=xyz }
      warning ACL rule ignored: Broker checks for rules with
                                action: 'access' and object: 'exchange'
                  but will never match with property set: { alternate=abc queuename=xyz }
      info ACL Plugin loaded

Three of the rules are invalid. The first invalid rule is rejected
because there are no rules that specify 'delete broker' regardless of
the properties. The other two rules are rejected because the property
sets in the ACL rule don't match any broker lookups.

The ACL module only issues a warning about these rules and continues to
operate. Users upgrading from previous versions should be concerned that
these rules never had any effect and should fix the rules to have the
property sets needed to allow or deny the intended broker events.

The next illustration shows the Debug-level log. Debug log level
includes information about constructing the rule tables, expanding
groups and keywords, connection and queue quotas, and connection black
and white lists.

      notice ACL: Read file "/home/chug/acl/svn-acl.acl"
      debug ACL: Group list: 1 groups found:
      debug ACL:   "x": a@QPID b2@QPID b3@QPID b@QPID
      debug ACL: name list: 7 names found:
      debug ACL:  * a@QPID a@qpid b2@QPID b3@QPID b@QPID b@qpid
      debug ACL: Rule list: 10 ACL rules found:
      debug ACL:    1 allow [*] delete broker
      warning ACL rule ignored: Broker never checks for rules with
                                action: 'delete' and object: 'broker'
      debug ACL:    2 allow [*] create queue name=abc
      debug ACL:    3 allow [*] create queue exchangename=xyz
      warning ACL rule ignored: Broker checks for rules with
                                action: 'create' and object: 'queue'
                         but will never match with property set: { exchangename=xyz }
      debug ACL:    4 allow [*] create connection host=1.1.1.1
      debug ACL:    5 allow [*] access exchange alternate=abc queuename=xyz
      warning ACL rule ignored: Broker checks for rules with
                                action: 'access' and object: 'exchange'
                         but will never match with property set: { alternate=abc queuename=xyz }
      debug ACL:    6 allow [*] access exchange queuename=xyz
      debug ACL:    7 allow [*] access exchange alternate=abc
      debug ACL:    8 allow [a@qpid] * * exchangename=123
      debug ACL:    9 allow [b@qpid] * *
      debug ACL:   10 allow [*] *
      debug ACL: connections quota: 0 rules found:
      debug ACL: queues quota: 0 rules found:
      debug ACL: Load Rules
      debug ACL: Processing 10 allow [*] *
      debug ACL: FoundMode allow
      debug ACL: Processing  9 allow [b@qpid] * *
      debug ACL: Adding actions {access,bind,consume,create,delete,move,publish,purge,
                                 redirect,reroute,unbind,update}
                     to objects {broker,connection,exchange,link,method,query,queue}
                     with props { }
                      for users {b@qpid}
      debug ACL: Processing  8 allow [a@qpid] * * exchangename=123
      debug ACL: Adding actions {access,bind,consume,create,delete,move,publish,purge,
                                 redirect,reroute,unbind,update}
                     to objects {broker,connection,exchange,link,method,query,queue}
                     with props { exchangename=123 }
                      for users {a@qpid}
      debug ACL: Processing  7 allow [*] access exchange alternate=abc
      debug ACL: Adding actions {access}
                     to objects {exchange}
                     with props { alternate=abc }
                      for users {*,a@QPID,a@qpid,b2@QPID,b3@QPID,b@QPID,b@qpid}
      debug ACL: Processing  6 allow [*] access exchange queuename=xyz
      debug ACL: Adding actions {access}
                     to objects {exchange}
                     with props { queuename=xyz }
                      for users {*,a@QPID,a@qpid,b2@QPID,b3@QPID,b@QPID,b@qpid}
      debug ACL: Processing  5 allow [*] access exchange alternate=abc queuename=xyz
      debug ACL: Processing  4 allow [*] create connection host=1.1.1.1
      debug ACL: Processing  3 allow [*] create queue exchangename=xyz
      debug ACL: Processing  2 allow [*] create queue name=abc
      debug ACL: Adding actions {create}
                     to objects {queue}
                     with props { name=abc }
                      for users {*,a@QPID,a@qpid,b2@QPID,b3@QPID,b@QPID,b@qpid}
      debug ACL: Processing  1 allow [*] delete broker
      debug ACL: global Connection Rule list : 1 rules found :
      debug ACL:    1 [ruleMode = allow {(1.1.1.1,1.1.1.1)}
      debug ACL: User Connection Rule lists : 0 user lists found :
      debug ACL: Transfer ACL is Enabled!
      info ACL Plugin loaded

The previous illustration is interesting because it shows the settings
as the *all* keywords are being expanded. However, that does not show
the information about what is actually going into the ACL lookup tables.

The next two illustrations show additional information provided by
Trace-level logs for ACL startup. The first shows a dump of the broker's
internal action/object/properties table. This table is authoratative.

      trace ACL: Definitions of action, object, (allowed properties) lookups
      trace ACL: Lookup  1: "User querying message timestamp setting  "
                              access   broker     ()
      trace ACL: Lookup  2: "AMQP 0-10 protocol received 'query'      "
                              access   exchange   (name)
      trace ACL: Lookup  3: "AMQP 0-10 query binding                  "
                              access   exchange   (name,routingkey,queuename)
      trace ACL: Lookup  4: "AMQP 0-10 exchange declare               "
                              access   exchange   (name,durable,autodelete,type,alternate)
      trace ACL: Lookup  5: "AMQP 1.0 exchange access                 "
                              access   exchange   (name,durable,type)
      trace ACL: Lookup  6: "AMQP 1.0 node resolution                 "
                              access   exchange   (name)
      trace ACL: Lookup  7: "Management method request                "
                              access   method     (name,schemapackage,schemaclass)
      trace ACL: Lookup  8: "Management agent method request          "
                              access   method     (name,schemapackage,schemaclass)
      trace ACL: Lookup  9: "Management agent query                   "
                              access   query      (name,schemaclass)
      trace ACL: Lookup 10: "QMF 'query queue' method                 "
                              access   queue      (name)
      trace ACL: Lookup 11: "AMQP 0-10 query                          "
                              access   queue      (name)
      trace ACL: Lookup 12: "AMQP 0-10 queue declare                  "
                              access   queue      (name,durable,autodelete,exclusive,alternate,
                                policytype,queuemaxsizelowerlimit,queuemaxsizeupperlimit,
                                queuemaxcountlowerlimit,queuemaxcountupperlimit)
      trace ACL: Lookup 13: "AMQP 1.0 queue access                    "
                              access   queue      (name,durable,autodelete,exclusive,alternate,
                                policytype,queuemaxsizelowerlimit,queuemaxsizeupperlimit,
                                queuemaxcountlowerlimit,queuemaxcountupperlimit)
      trace ACL: Lookup 14: "AMQP 1.0 node resolution                 "
                              access   queue      (name)
      trace ACL: Lookup 15: "AMQP 0-10 or QMF bind request            "
                              bind     exchange   (name,routingkey,queuename)
      trace ACL: Lookup 16: "AMQP 1.0 new outgoing link from exchange "
                              bind     exchange   (name,routingkey,queuename)
      trace ACL: Lookup 17: "AMQP 0-10 subscribe request              "
                              consume  queue      (name)
      trace ACL: Lookup 18: "AMQP 1.0 new outgoing link from queue    "
                              consume  queue      (name)
      trace ACL: Lookup 19: "TCP/IP connection creation               "
                              create   connection (host)
      trace ACL: Lookup 20: "Create exchange                          "
                              create   exchange   (name,durable,autodelete,type,alternate)
      trace ACL: Lookup 21: "Interbroker link creation                "
                              create   link       ()
      trace ACL: Lookup 22: "Interbroker link creation                "
                              create   link       ()
      trace ACL: Lookup 23: "Create queue                             "
                              create   queue      (name,durable,autodelete,exclusive,
                                alternate,policytype,paging,
                                queuemaxsizelowerlimit,queuemaxsizeupperlimit,
                                queuemaxcountlowerlimit,queuemaxcountupperlimit,
                                filemaxsizelowerlimit,filemaxsizeupperlimit,
                                filemaxcountlowerlimit,filemaxcountupperlimit,
                                pageslowerlimit,pagesupperlimit,
                                pagefactorlowerlimit,pagefactorupperlimit)
      trace ACL: Lookup 24: "Delete exchange                          "
                              delete   exchange   (name,durable,type,alternate)
      trace ACL: Lookup 25: "Delete queue                             "
                              delete   queue      (name,durable,autodelete,exclusive,
                                alternate,policytype)
      trace ACL: Lookup 26: "Management 'move queue' request          "
                              move     queue      (name,queuename)
      trace ACL: Lookup 27: "AMQP 0-10 received message processing    "
                              publish  exchange   (name,routingkey)
      trace ACL: Lookup 28: "AMQP 1.0 establish sender link to queue  "
                              publish  exchange   (routingkey)
      trace ACL: Lookup 29: "AMQP 1.0 received message processing     "
                              publish  exchange   (name,routingkey)
      trace ACL: Lookup 30: "Management 'purge queue' request         "
                              purge    queue      (name)
      trace ACL: Lookup 31: "Management 'purge queue' request         "
                              purge    queue      (name)
      trace ACL: Lookup 32: "Management 'redirect queue' request      "
                              redirect queue      (name,queuename)
      trace ACL: Lookup 33: "Management 'reroute queue' request       "
                              reroute  queue      (name,exchangename)
      trace ACL: Lookup 34: "Management 'unbind exchange' request     "
                              unbind   exchange   (name,routingkey,queuename)
      trace ACL: Lookup 35: "User modifying message timestamp setting "
                              update   broker     ()

The final illustration shows a dump of every rule for every user in the
ACL database. It includes the user name, action, object, original ACL
rule number, allow or deny status, and a cross reference indicating
which Lookup Events the rule could possibly satisfy.

Note that rules identified by *User: \** are the rules in effect for
users otherwise unnamed in the ACL file.

      trace ACL: Decision rule cross reference
      trace ACL: User: b@qpid   access   broker
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (1)
      trace ACL: User: *        access   exchange
                            Rule: [rule 6 ruleMode = allow props{ queuename=xyz }]
                                  may match Lookups : (3)
      trace ACL: User: *        access   exchange
                            Rule: [rule 7 ruleMode = allow props{ alternate=abc }]
                                  may match Lookups : (4)
      trace ACL: User: a@QPID   access   exchange
                            Rule: [rule 6 ruleMode = allow props{ queuename=xyz }]
                                  may match Lookups : (3)
      trace ACL: User: a@QPID   access   exchange
                            Rule: [rule 7 ruleMode = allow props{ alternate=abc }]
                                  may match Lookups : (4)
      trace ACL: User: a@qpid   access   exchange
                            Rule: [rule 6 ruleMode = allow props{ queuename=xyz }]
                                  may match Lookups : (3)
      trace ACL: User: a@qpid   access   exchange
                            Rule: [rule 7 ruleMode = allow props{ alternate=abc }]
                                  may match Lookups : (4)
      trace ACL: User: b2@QPID  access   exchange
                            Rule: [rule 6 ruleMode = allow props{ queuename=xyz }]
                                  may match Lookups : (3)
      trace ACL: User: b2@QPID  access   exchange
                            Rule: [rule 7 ruleMode = allow props{ alternate=abc }]
                                  may match Lookups : (4)
      trace ACL: User: b3@QPID  access   exchange
                            Rule: [rule 6 ruleMode = allow props{ queuename=xyz }]
                                  may match Lookups : (3)
      trace ACL: User: b3@QPID  access   exchange
                            Rule: [rule 7 ruleMode = allow props{ alternate=abc }]
                                  may match Lookups : (4)
      trace ACL: User: b@QPID   access   exchange
                            Rule: [rule 6 ruleMode = allow props{ queuename=xyz }]
                                  may match Lookups : (3)
      trace ACL: User: b@QPID   access   exchange
                            Rule: [rule 7 ruleMode = allow props{ alternate=abc }]
                                  may match Lookups : (4)
      trace ACL: User: b@qpid   access   exchange
                            Rule: [rule 6 ruleMode = allow props{ queuename=xyz }]
                                  may match Lookups : (3)
      trace ACL: User: b@qpid   access   exchange
                            Rule: [rule 7 ruleMode = allow props{ alternate=abc }]
                                  may match Lookups : (4)
      trace ACL: User: b@qpid   access   exchange
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (2,3,4,5,6)
      trace ACL: User: b@qpid   access   method
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (7,8)
      trace ACL: User: b@qpid   access   query
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (9)
      trace ACL: User: b@qpid   access   queue
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (10,11,12,13,14)
      trace ACL: User: b@qpid   bind     exchange
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (15,16)
      trace ACL: User: b@qpid   consume  queue
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (17,18)
      trace ACL: User: b@qpid   create   connection
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (19)
      trace ACL: User: b@qpid   create   exchange
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (20)
      trace ACL: User: b@qpid   create   link
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (21,22)
      trace ACL: User: *        create   queue
                            Rule: [rule 2 ruleMode = allow props{ name=abc }]
                                  may match Lookups : (23)
      trace ACL: User: a@QPID   create   queue
                            Rule: [rule 2 ruleMode = allow props{ name=abc }]
                                  may match Lookups : (23)
      trace ACL: User: a@qpid   create   queue
                            Rule: [rule 2 ruleMode = allow props{ name=abc }]
                                  may match Lookups : (23)
      trace ACL: User: b2@QPID  create   queue
                            Rule: [rule 2 ruleMode = allow props{ name=abc }]
                                  may match Lookups : (23)
      trace ACL: User: b3@QPID  create   queue
                            Rule: [rule 2 ruleMode = allow props{ name=abc }]
                                  may match Lookups : (23)
      trace ACL: User: b@QPID   create   queue
                            Rule: [rule 2 ruleMode = allow props{ name=abc }]
                                  may match Lookups : (23)
      trace ACL: User: b@qpid   create   queue
                            Rule: [rule 2 ruleMode = allow props{ name=abc }]
                                  may match Lookups : (23)
      trace ACL: User: b@qpid   create   queue
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (23)
      trace ACL: User: b@qpid   delete   exchange
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (24)
      trace ACL: User: b@qpid   delete   queue
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (25)
      trace ACL: User: b@qpid   move     queue
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (26)
      trace ACL: User: b@qpid   publish  exchange
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (27,28,29)
      trace ACL: User: b@qpid   purge    queue
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (30,31)
      trace ACL: User: b@qpid   redirect queue
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (32)
      trace ACL: User: a@qpid   reroute  queue
                            Rule: [rule 8 ruleMode = allow props{ exchangename=123 }]
                                  may match Lookups : (33)
      trace ACL: User: b@qpid   reroute  queue
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (33)
      trace ACL: User: b@qpid   unbind   exchange
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (34)
      trace ACL: User: b@qpid   update   broker
                            Rule: [rule 9 ruleMode = allow props{ }]
                                  may match Lookups : (35)

## <span class="header-section-number">1.3</span> User Connection and Queue Quotas

The ACL module enforces various quotas and thereby limits user activity.

### <span class="header-section-number">1.3.1</span> Connection Count Limits

The ACL module creates broker command line switches that set limits on
the number of concurrent connections allowed per user or per client host
address. These settings are not specified in the ACL file.

        --max-connections           N
        --connection-limit-per-user N
        --connection-limit-per-ip   N
                        

`--max-connections` specifies an upper limit for all user connections.

`--connection-limit-per-user` specifies an upper limit for each user
based on the authenticated user name. This limit is enforced regardless
of the client IP address from which the connection originates.

`--connection-limit-per-ip` specifies an upper limit for connections for
all users based on the originating client IP address. This limit is
enforced regardless of the user credentials presented with the
connection.

-   Note that addresses using different transports are counted
    separately even though the originating host is actually the same
    physical machine. In the setting illustrated above a host would
    allow N\_IP connections from [::1] IPv6 transport localhost and
    another N\_IP connections from [127.0.0.1] IPv4 transport localhost.
-   The connection-limit-per-ip and connection-limit-per-user counts are
    active simultaneously. From a given client system users may be
    denied access to the broker by either connection limit.

The 0.22 C++ Broker ACL module accepts fine grained per-user connection
limits through quota rules in the ACL file.

        quota connections 10 admins userX@QPID
                        

-   User all receives the value passed by the command line
    switch --connection-limit-per-user .
-   Values specified in the ACL rule for user all overwrite the value
    specified on the command line if any.
-   Connection quotas values are determined by first searching for the
    authenticated user name. If that user name is not specified then the
    value for user all is used. If user all is not specified then the
    connection is denied.
-   The connection quota values range from 0..65530 inclusive. A value
    of zero disables connections from that user.
-   A user's quota may be specified many times in the ACL rule file.
    Only the last value specified is retained and enforced.
-   Per-user connection quotas are disabled when two conditions are
    true: 1) No --connection-limit-per-user command line switch and 2)
    No quota connections rules in the ACL file. Per-user connections are
    always counted even if connection quotas are not enforced. This
    supports ACL file reloading that may subsequently enable per-user
    connection quotas.
-   An ACL file reload may lower a user's connection quota value to a
    number lower than the user's current connection count. In that case
    the active connections remain unaffected. New connections are denied
    until that user closes enough of his connections so that his count
    falls below the configured limit.

### <span class="header-section-number">1.3.2</span> Connection Limits by Host Name

The 0.30 C++ Broker ACL module adds the ability to create allow and deny
lists of the TCP/IP hosts from which users may connect. The rule accepts
these forms:

        acl allow user create connection host=host1
        acl allow user create connection host=host1,host2
        acl deny  user create connection host=all
                        

Using the form `host=host1` specifies a single host. With a single host
the name may resolve to multiple TCP/IP addresses. For example
*localhost* resolves to both *127.0.0.1* and *::1* and possibly many
other addresses. A connection from any of the addresses associated with
this host matches the rule and the connection is allowed or denied
accordingly.

Using the form `host=host1,host2` specifies a range of TCP/IP addresses.
With a host range each host must resolve to a single TCP/IP address and
the second address must be numerically larger than the first. A
connection from any host where host \>= host1 and host \<= host2 match
the rule and the connection is allowed or denied accordingly.

Using the form `host=all` specifies all TCP/IP addresses. A connection
from any host matches the rule and the connection is allowed or denied
accordingly.

Connection denial is only applied to incoming TCP/IP connections. Other
socket types are not subjected to nor denied by range checks.

Connection creation rules are divided into three categories:

User = all, host != all

These define global rules and are applied before any specific user
rules. These rules may be used to reject connections before any AMPQ
protocol is run and before any user names have been negotiated.

User != all, host = any legal host or 'all'

These define user rules. These rules are applied after the global rules
and after the AMQP protocol has negotiated user identities.

User = all, host = all

This rule defines what to do if no other rule matches. The default value
is "ALLOW". Only one rule of this type may be defined.

The following example illustrates how this feature can be used.

        group admins alice bob chuck
        group Company1 c1_usera c1_userb
        group Company2 c2_userx c2_usery c2_userz
        acl allow admins   create connection host=localhost
        acl allow admins   create connection host=10.0.0.0,10.255.255.255
        acl allow admins   create connection host=192.168.0.0,192.168.255.255
        acl allow admins   create connection host=[fc00::],[fc00::ff]
        acl allow Company1 create connection host=company1.com
        acl deny  Company1 create connection host=all
        acl allow Company2 create connection host=company2.com
        acl deny  Company2 create connection host=all
                        

In this example admins may connect from localhost or from any system on
the 10.0.0.0/24, 192.168.0.0/16, and fc00::/7 subnets. Company1 users
may connect only from company1.com and Company2 users may connect only
from company2.com. However, this example has a flaw. Although the admins
group has specific hosts from which it is allowed to make connections it
is not blocked from connecting from anywhere. The Company1 and Company2
groups are blocked appropriately. This ACL file may be rewritten as
follows:

        group admins alice bob chuck
        group Company1 c1_usera c1_userb
        group Company2 c2_userx c2_usery c2_userz
        acl allow admins   create connection host=localhost
        acl allow admins   create connection host=10.0.0.0,10.255.255.255
        acl allow admins   create connection host=192.168.0.0,192.168.255.255
        acl allow admins   create connection host=[fc00::],[fc00::ff]
        acl allow Company1 create connection host=company1.com
        acl allow Company2 create connection host=company2.com
        acl deny  all      create connection host=all
                        

Now admins are blocked from connecting from anywhere but their allowed
hosts.

### <span class="header-section-number">1.3.3</span> Queue Limits

The ACL module creates a broker command line switch that set limits on
the number of queues each user is allowed to create. This settings is
not specified in the ACL file.

        --max-queues-per-user N
                        

The queue limit is set for all users on the broker.

The 0.22 C++ Broker ACL module accepts fine grained per-user queue
limits through quota rules in the ACL file.

        quota queues 10 admins userX@QPID
                        

-   User all receives the value passed by the command line
    switch --max-queues-per-user .
-   Values specified in the ACL rule for user all overwrite the value
    specified on the command line if any.
-   Queue quotas values are determined by first searching for the
    authenticated user name. If that user name is not specified then the
    value for user all is used. If user all is not specified then the
    queue creation is denied.
-   The queue quota values range from 0..65530 inclusive. A value of
    zero disables queue creation by that user.
-   A user's quota may be specified many times in the ACL rule file.
    Only the last value specified is retained and enforced.
-   Per-user queue quotas are disabled when two conditions are true: 1)
    No --queue-limit-per-user command line switch and 2) No quota queues
    rules in the ACL file. Per-user queue creations are always counted
    even if queue quotas are not enforced. This supports ACL file
    reloading that may subsequently enable per-user queue quotas.
-   An ACL file reload may lower a user's queue quota value to a number
    lower than the user's current queue count. In that case the active
    queues remain unaffected. New queues are denied until that user
    closes enough of his queues so that his count falls below the
    configured limit.

## <span class="header-section-number">1.4</span> Encryption using SSL

Encryption and certificate management for `qpidd` is provided by
Mozilla's Network Security Services Library (NSS).

1.  You will need a certificate that has been signed by a Certification
    Authority (CA). This certificate will also need to be trusted by
    your client. If you require client authentication in addition to
    server authentication, the client's certificate will also need to be
    signed by a CA and trusted by the broker.

    In the broker, SSL is provided through the `ssl.so` module. This
    module is installed and loaded by default in Qpid. To enable the
    module, you need to specify the location of the database containing
    the certificate and key to use. This is done using the `ssl-cert-db`
    option.

    The certificate database is created and managed by the Mozilla
    Network Security Services (NSS) `certutil` tool. Information on this
    utility can be found on the [Mozilla
    website](http://www.mozilla.org/projects/security/pki/nss/tools/certutil.html),
    including tutorials on setting up and testing SSL connections. The
    certificate database will generally be password protected. The
    safest way to specify the password is to place it in a protected
    file, use the password file when creating the database, and specify
    the password file with the `ssl-cert-password-file` option when
    starting the broker.

    The following script shows how to create a certificate database
    using certutil:

        mkdir ${CERT_DIR}
        certutil -N -d ${CERT_DIR} -f ${CERT_PW_FILE}
        certutil -S -d ${CERT_DIR} -n ${NICKNAME} -s "CN=${NICKNAME}" -t "CT,," -x -f ${CERT_PW_FILE} -z /usr/bin/certutil

    When starting the broker, set `ssl-cert-password-file` to the value
    of `${CERT_PW_FILE}`, set `ssl-cert-db` to the value of
    `${CERT_DIR}`, and set `ssl-cert-name` to the value of
    `${NICKNAME}`.

2.  The following SSL options can be used when starting the broker:

    `--ssl-use-export-policy`  
    Use NSS export policy

    `--ssl-cert-password-file PATH`  
    Required. Plain-text file containing password to use for accessing
    certificate database.

    `--ssl-cert-db PATH`  
    Required. Path to directory containing certificate database.

    `--ssl-cert-name NAME`  
    Name of the certificate to use. Default is `localhost.localdomain`.

    `--ssl-port NUMBER`  
    Port on which to listen for SSL connections. If no port is
    specified, port 5671 is used.

    `--ssl-require-client-authentication`  
    Require SSL client authentication (i.e. verification of a client
    certificate) during the SSL handshake. This occurs before SASL
    authentication, and is independent of SASL.

    This option enables the `EXTERNAL` SASL mechanism for SSL
    connections. If the client chooses the `EXTERNAL` mechanism, the
    client's identity is taken from the validated SSL certificate, using
    the `CN`literal\>, and appending any `DC`literal\>s to create the
    domain. For instance, if the certificate contains the properties
    `CN=bob`, `DC=acme`, `DC=com`, the client's identity is
    `bob@acme.com`.

    If the client chooses a different SASL mechanism, the identity take
    from the client certificate will be replaced by that negotiated
    during the SASL handshake.

    `--ssl-sasl-no-dict`  
    Do not accept SASL mechanisms that can be compromised by dictionary
    attacks. This prevents a weaker mechanism being selected instead of
    `EXTERNAL`, which is not vulnerable to dictionary attacks.

    Also relevant is the `--require-encryption` broker option. This will
    cause `qpidd` to only accept encrypted connections.

C++ clients:  
1.  In C++ clients, SSL is implemented in the `sslconnector.so` module.
    This module is installed and loaded by default in Qpid.

    The following options can be specified for C++ clients using
    environment variables:

    SSL Client Environment Variables for C++ clients

    SSL Client Options for C++ clients

    `QPID_SSL_USE_EXPORT_POLICY`

    Use NSS export policy

    `QPID_SSL_CERT_PASSWORD_FILE PATH`

    File containing password to use for accessing certificate database

    `QPID_SSL_CERT_DB PATH`

    Path to directory containing certificate database

    `QPID_SSL_CERT_NAME NAME`

    Name of the certificate to use. When SSL client authentication is
    enabled, a certificate name should normally be provided.

2.  When using SSL connections, clients must specify the location of the
    certificate database, a directory that contains the client's
    certificate and the public key of the Certificate Authority. This
    can be done by setting the environment variable `QPID_SSL_CERT_DB`
    to the full pathname of the directory. If a connection uses SSL
    client authentication, the client's password is also needed—the
    password should be placed in a protected file, and the
    `QPID_SSL_CERT_PASSWORD_FILE` variable should be set to the location
    of the file containing this password.

3.  To open an SSL enabled connection in the Qpid Messaging API, set the
    `protocol` connection option to `ssl`.

Java clients:  
1.  For both server and client authentication, import the trusted CA to
    your trust store and keystore and generate keys for them. Create a
    certificate request using the generated keys and then create a
    certificate using the request. You can then import the signed
    certificate into your keystore. Pass the following arguments to the
    Java JVM when starting your client:

        -Djavax.net.ssl.keyStore=/home/bob/ssl_test/keystore.jks
        -Djavax.net.ssl.keyStorePassword=password
        -Djavax.net.ssl.trustStore=/home/bob/ssl_test/certstore.jks
        -Djavax.net.ssl.trustStorePassword=password

2.  For server side authentication only, import the trusted CA to your
    trust store and pass the following arguments to the Java JVM when
    starting your client:

        -Djavax.net.ssl.trustStore=/home/bob/ssl_test/certstore.jks
        -Djavax.net.ssl.trustStorePassword=password

3.  Java clients must use the SSL option in the connection URL to enable
    SSL encryption, e.g.

        amqp://username:password@clientid/test?brokerlist='tcp://localhost:5672?ssl='true''

4.  If you need to debug problems in an SSL connection, enable Java's
    SSL debugging by passing the argument `-Djavax.net.debug=ssl` to the
    Java JVM when starting your client.


