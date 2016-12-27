# ACL Syntax

## Syntax [1]

### Comments

-   A line starting with the `#` character is considered a comment and
    is ignored.

-   Embedded comments and trailing comments are not allowed. The `#` is
    commonly found in routing keys and other AMQP literals which occur
    naturally in ACL rule specifications.

### White space

-   Empty lines and lines that contain only whitespace (' ', '\\f',
    '\\n', '\\r', '\\t', '\\v') are ignored.

-   Additional whitespace between and after tokens is allowed.

-   Group and Acl definitions must start with `group` and `acl`
    respectively and with no preceding whitespace.

### Character set

-   ACL files use 7-bit ASCII characters only

-   Group names may contain only

    -   [a-z]
    -   [A-Z]
    -   [0-9]
    -   '-'
        hyphen
    -   '\_'
        underscore

-   Individual user names may contain only

    -   [a-z]
    -   [A-Z]
    -   [0-9]
    -   '-'
        hyphen
    -   '\_'
        underscore
    -   '.'
        period
    -   '@'
        ampersand
    -   '/'
        slash

### Case sensitivity

-   All tokens are case sensitive. `name1` is not the same as `Name1`
    and `create` is not the same as `CREATE`.

### Line continuation

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

### Line length

-   ACL file lines are limited to 1024 characters.

### Keywords

ACL reserves several words for convenience and for context sensitive
substitution.
##### The `all` Keyword

The keyword
all
is reserved. It may be used in ACL rules to match all individuals and
groups, all actions, or all objects.
-   acl allow all create queue
-   acl allow bob@QPID all queue
-   acl allow bob@QPID create all

#### User name and domain name keywords

In the C++ Broker 0.20 a simple set of user name and domain name
substitution variable keyword tokens is defined. This provides
administrators with an easy way to describe private or shared resources.

Symbol substitution is allowed in the ACL file anywhere that text is
supplied for a property value.

In the following table an authenticated user named bob.user@QPID.COM has
his substitution keywords expanded.

  Keyword           Expansion
  ----------------- ----------------------
  `${userdomain}`   bob\_user\_QPID\_COM
  `${user}`         bob\_user
  `${domain}`       QPID\_COM

  : ACL User Name and Domain Name Substitution Keywords

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

### Wildcards

ACL privides two types of wildcard matching to provide flexibility in
writing rules.

#### Property value wildcard

Text specifying a property value may end with a single trailing `*`
character. This is a simple wildcard match indicating that strings which
match up to that point are matches for the ACL property rule. An ACL
rule such as

        acl allow bob@QPID create queue name=bob*

allow user bob@QPID to create queues named bob1, bob2, bobQueue3, and so
on.

#### Topic routing key wildcard

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

-   \*
    matches one field
-   \#
    matches zero or more fields

Suppose an ACL rule file is:

        acl allow-log uHash1@COMPANY publish exchange name=X routingkey=a.#.b
        acl deny all all
                      

When user uHash1@COMPANY attempts to publish to exchange X the ACL will
return these results:

  routingkey in publish to exchange X   result
  ------------------------------------- -----------
  `a.b`                                 allow-log
  `a.x.b`                               allow-log
  `a.x.y.zz.b`                          allow-log
  `a.b.`                                deny
  `q.x.b`                               deny

  : Topic Exchange Wildcard Match Examples

## Syntax [2]

### ACL Syntax

ACL rules must be on a single line and follow this syntax:

        user = username[/domain[@realm]]
        user-list = user1 user2 user3 ...
        group-name-list = group1 group2 group3 ...
        
        group <group-name> = [user-list] [group-name-list]
        
        permission = [allow | allow-log | deny | deny-log]
        action = [consume | publish | create | access | 
                  bind | unbind | delete | purge | update]
        object = [queue | exchange | broker | link | method]
        property = [name | durable | owner | routingkey | 
                    autodelete | exclusive |type | 
            alternate | queuename | 
            schemapackage | schemaclass | 
            queuemaxsizelowerlimit  | 
            queuemaxsizeupperlimit  |
                    queuemaxcountlowerlimit | 
            queuemaxcountupperlimit |
                    filemaxsizelowerlimit   | 
            filemaxsizeupperlimit   |
                    filemaxcountlowerlimit  | 
            filemaxcountupperlimit ]
        
        acl permission {<group-name>|<user-name>|"all"} {action|"all"} [object|"all" 
                    [property=<property-value> ...]]

        quota-spec = [connections | queues]
        quota quota-spec N {<group-name>|<user-name>|"all"}
                    [{<group-name>|<user-name>|"all"}]

ACL rules can also include a single object name (or the keyword `all`)
and one or more property name value pairs in the form `property=value`

The following tables show the possible values for `permission`,
`action`, `object`, and `property` in an ACL rules file.

  ------------- ------------------------------------------------------
  `allow`       Allow the action
  `allow-log`   Allow the action and log the action in the event log
  `deny`        Deny the action
  `deny-log`    Deny the action and log the action in the event log
  ------------- ------------------------------------------------------

  : ACL Rules: permission

  ----------- -------------------------------------------------------------------------------------------------------------------------------
  `consume`   Applied when subscriptions are created
  `publish`   Applied on a per message basis to verify that the user has rights to publish to the given exchange with the given routingkey.
  `create`    Applied when an object is created, such as bindings, queues, exchanges, links
  `access`    Applied when an object is read or accessed
  `bind`      Applied when objects are bound together
  `unbind`    Applied when objects are unbound
  `delete`    Applied when objects are deleted
  `purge`     Similar to delete but the action is performed on more than one object
  `update`    Applied when an object is updated
  ----------- -------------------------------------------------------------------------------------------------------------------------------

  : ACL Rules:action

  ------------ --------------------------------------
  `queue`      A queue
  `exchange`   An exchange
  `broker`     The broker
  `link`       A federation or inter-broker link
  `method`     Management or agent or broker method
  ------------ --------------------------------------

  : ACL Rules:object

  Property                    Type      Description                                                                      Usage
  --------------------------- --------- -------------------------------------------------------------------------------- -------------------------------------------------------------------
  `name`                      String    Object name, such as a queue name or exchange name.                              
  `durable`                   Boolean   Indicates the object is durable                                                  CREATE QUEUE, CREATE EXCHANGE, ACCESS QUEUE, ACCESS EXCHANGE
  `routingkey`                String    Specifies routing key                                                            BIND EXCHANGE, UNBIND EXCHANGE, ACCESS EXCHANGE, PUBLISH EXCHANGE
  `autodelete`                Boolean   Indicates whether or not the object gets deleted when the connection is closed   CREATE QUEUE, ACCESS QUEUE
  `exclusive`                 Boolean   Indicates the presence of an `exclusive` flag                                    CREATE QUEUE, ACCESS QUEUE
  `type`                      String    Type of exchange, such as topic, fanout, or xml                                  CREATE EXCHANGE, ACCESS EXCHANGE
  `alternate`                 String    Name of the alternate exchange                                                   CREATE EXCHANGE, CREATE QUEUE, ACCESS EXCHANGE, ACCESS QUEUE
  `queuename`                 String    Name of the queue                                                                ACCESS EXCHANGE, BIND EXCHANGE, UNBIND EXCHANGE
  `schemapackage`             String    QMF schema package name                                                          ACCESS METHOD
  `schemaclass`               String    QMF schema class name                                                            ACCESS METHOD
  `queuemaxsizelowerlimit`    Integer   Minimum value for queue.max\_size (memory bytes)                                 CREATE QUEUE, ACCESS QUEUE
  `queuemaxsizeupperlimit`    Integer   Maximum value for queue.max\_size (memory bytes)                                 CREATE QUEUE, ACCESS QUEUE
  `queuemaxcountlowerlimit`   Integer   Minimum value for queue.max\_count (messages)                                    CREATE QUEUE, ACCESS QUEUE
  `queuemaxcountupperlimit`   Integer   Maximum value for queue.max\_count (messages)                                    CREATE QUEUE, ACCESS QUEUE
  `filemaxsizelowerlimit`     Integer   Minimum value for file.max\_size (64kb pages)                                    CREATE QUEUE, ACCESS QUEUE
  `filemaxsizeupperlimit`     Integer   Maximum value for file.max\_size (64kb pages)                                    CREATE QUEUE, ACCESS QUEUE
  `filemaxcountlowerlimit`    Integer   Minimum value for file.max\_count (files)                                        CREATE QUEUE, ACCESS QUEUE
  `filemaxcountupperlimit`    Integer   Maximum value for file.max\_count (files)                                        CREATE QUEUE, ACCESS QUEUE

  : ACL Rules:property

#### ACL Action-Object-Property Tuples

Not every ACL action is applicable to every ACL object. Furthermore, not
every property may be specified for every action-object pair. The
following table enumerates which action and object pairs are allowed.
The table also lists which optional ACL properties are allowed to
qualify action-object pairs.

The *access* action is called with different argument lists for the
*exchange* and *queue* objects. A separate column shows the AMQP 0.10
method that the Access ACL rule is satisfying. Write separate rules with
the additional arguments for the *declare* and *bind* methods and
include these rules in the ACL file before the rules for the *query*
method.

  Action    Object     Properties                                                                                                                                                                                                                                   Method
  --------- ---------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------
  access    broker     
  access    exchange   name type alternate durable                                                                                                                                                                                                                  declare
  access    exchange   name queuename routingkey                                                                                                                                                                                                                    bound
  access    exchange   name                                                                                                                                                                                                                                         query
  access    method     name schemapackage schemaclass                                                                                                                                                                                                               
  access    queue      name alternate durable exclusive autodelete policy queuemaxsizelowerlimit queuemaxsizeupperlimit queuemaxcountlowerlimit queuemaxcountupperlimit filemaxsizelowerlimit filemaxsizeupperlimit filemaxcountlowerlimit filemaxcountupperlimit   declare
  access    queue      name                                                                                                                                                                                                                                         query
  bind      exchange   name queuename routingkey                                                                                                                                                                                                                    
  consume   queue      name                                                                                                                                                                                                                                         
  create    exchange   name type alternate durable                                                                                                                                                                                                                  
  create    link       name                                                                                                                                                                                                                                         
  create    queue      name alternate durable exclusive autodelete policy queuemaxsizelowerlimit queuemaxsizeupperlimit queuemaxcountlowerlimit queuemaxcountupperlimit filemaxsizelowerlimit filemaxsizeupperlimit filemaxcountlowerlimit filemaxcountupperlimit   
  delete    exchange   name                                                                                                                                                                                                                                         
  delete    queue      name                                                                                                                                                                                                                                         
  publish   exchange   name routingkey                                                                                                                                                                                                                              
  purge     queue      name                                                                                                                                                                                                                                         
  unbind    exchange   name queuename routingkey                                                                                                                                                                                                                    
  update    broker                                                                                                                                                                                                                                                  

  : ACL Properties Allowed for each Action and Object
