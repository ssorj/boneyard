# Authorization

In Qpid, Authorization specifies which actions can be performed by each
authenticated user using an Access Control List (ACL).

Use the `--acl-file` command to load the access control list. The
filename should have a `.acl` extension:

        $ qpidd --acl-file 

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

## ACL rule matching

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

## Specifying permissions

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
