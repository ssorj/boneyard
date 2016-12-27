# Authentication

[Up to Security](security.html)

AMQP uses the Simple Authentication and Security Layer (SASL) to
authenticate client connections to the broker. SASL is a framework
that supports a variety of authentication methods. For secure
applications, we suggest `CRAM-MD5`, `DIGEST-MD5`, or `GSSAPI`. The
`ANONYMOUS` method is not secure. The `PLAIN` method is secure only
when used together with SSL.

Both the Qpid broker and Qpid clients use the
[Cyrus SASL library](http://cyrusimap.web.cmu.edu/), a full-featured
authentication framework, which offers many configuration
options. This section shows how to configure users for authentication
with SASL, which is sufficient when using `SASL PLAIN`. If you are not
using SSL, you should configure SASL to use `CRAM-MD5`, `DIGEST-MD5`,
or `GSSAPI` which provides Kerberos authentication. For information on
configuring these and other options in SASL, see the Cyrus SASL
documentation.

> **Important**
>
> The `SASL PLAIN` method sends passwords in cleartext, and is
> vulnerable to man-in-the-middle attacks unless SSL (Secure Socket
> Layer) is also used (see [SSL](ssl.html)).
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

## Configuring SASL

On Linux systems, the SASL configuration file is generally found in
`/etc/sasl2/qpidd.conf` or `/usr/lib/sasl2/qpidd.conf`.

The SASL database contains user names and passwords for SASL. In SASL,
a user may be associated with a realm. The Qpid broker authenticates
users in the `QPID` realm by default, but it can be set to a different
realm using the `realm` option:

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
> is compromised, so are all of the passwords that it stores. This is the
> reason that the qpidd user is the only user that can read the
> database. If you modify permissions, be careful not to expose the SASL
> database.

Add new users to the database by using the `saslpasswd2` command,
which specifies a realm and a user ID. A user ID takes the form `@.`.

    # saslpasswd2 -f /var/lib/qpidd/qpidd.sasldb -u  

XXX the above appears to be messed up

To list the users in the SASL database, use `sasldblistusers2`:

    # sasldblistusers2 -f /var/lib/qpidd/qpidd.sasldb

If you are using `PLAIN` authentication, users who are in the database
can now connect with their user name and password. This is secure only
if you are using SSL. If you are using a more secure form of
authentication, please consult your SASL documentation for information
on configuring the options you need.

## Kerberos

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
primary, the instance, and the realm. A typical Kerberos V5 (XXX a
typical V5 what?) has the format `primary/instance@REALM`. For a Qpid
broker, the primary is `qpidd`, the instance is the fully qualified
domain name, which you can obtain using `hostname --fqdn`, and the
REALM is the Kerberos domain realm. By default, this realm is `QPID`,
but a different realm can be specified in qpid.conf (XXX qpidd.conf?),
e.g.:

    realm=EXAMPLE.COM

For instance, if the fully qualified domain name is
`dublduck.example.com` and the Kerberos domain realm is `EXAMPLE.COM`,
then the principal name is `qpidd/dublduck.example.com@EXAMPLE.COM`.

The following script creates a principal for qpidd:

    FDQN=`hostname --fqdn`
    REALM="EXAMPLE.COM"
    kadmin -r $REALM  -q "addprinc -randkey -clearpolicy qpidd/$FQDN"

Now create a Kerberos keytab file for the Qpid broker. The Qpid broker
must have read access to the keytab file. The following script creates
a keytab file and allows the broker read access:

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
:   Forces the SASL GASSPI client to obtain the kerberos credentials
    explicitly instead of obtaining from the "subject" that owns the
    current thread.

-Djava.security.auth.login.config=myjas.conf
:   Specifies the jass configuration file. Here is a sample JASS
    configuration file:

        com.sun.security.jgss.initiate {
            com.sun.security.auth.module.Krb5LoginModule required useTicketCache=true;
        };

-Dsun.security.krb5.debug=true
:   Enables detailed debug info for troubleshooting

The client's Connection URL must specify the following Kerberos-specific
broker properties:

-   `sasl_mechs` must be set to `GSSAPI`.

-   `sasl_protocol` must be set to the principal for the qpidd broker,
    e.g. `qpidd`/

-   `sasl_server` must be set to the host for the SASL server, e.g.
    `sasl.com`.

Here is a sample connection URL for a Kerberos connection:

    amqp://guest@clientid/testpath?brokerlist='tcp://localhost:5672?sasl_mechs='GSSAPI'&sasl_protocol='qpidd'&sasl_server='<server-host-name>''

## Authentication [from the Running a Broker section XXX]

### Linux

The PLAIN authentication is done on a username+password, which is stored
in the sasldb\_path file. Usernames and passwords can be added to the
file using the command:

    saslpasswd2 -f /var/lib/qpidd/qpidd.sasldb -u <REALM> <USER>

The REALM is important and should be the same as the --auth-realm option
to the broker. This lets the broker properly find the user in the sasldb
file.

Existing user accounts may be listed with:

    sasldblistusers2 -f /var/lib/qpidd/qpidd.sasldb

NOTE: The sasldb file must be readable by the user running the qpidd
daemon, and should be readable only by that user.

### Windows

On Windows, the users are authenticated against the local machine. You
should add the appropriate users using the standard Windows tools
(Control Panel-\>User Accounts). To run many of the examples, you will
need to create a user "guest" with password "guest".

If you cannot or do not want to create new users, you can run without
authentication by specifying the no-auth option to the broker.

## SASL

### Standard Mechanisms

[](http://en.wikipedia.org/wiki/Simple_Authentication_and_Security_Layer#SASL_mechanisms)

This table list the various SASL mechanisms that each component
supports. The version listed shows when this functionality was added to
the product.

  --------------- ----------- ---------- ------------ ---------- ----------------- -------
  Component       ANONYMOUS   CRAM-MD5   DIGEST-MD5   EXTERNAL   GSSAPI/Kerberos   PLAIN
  C++ Broker      M3[?]       M3[?,?]                            M3[?,?]           M1
  C++ Client      M3[?]                                                            M1
  Java Broker                 M1                                                   M1
  Java Client                 M1                                                   M1
  .Net Client     M2          M2         M2           M2                           M2
  Python Client                                                                    ?
  Ruby Client                                                                      ?
  --------------- ----------- ---------- ------------ ---------- ----------------- -------

  : SASL Mechanism Support

1: Support for these will be in M3 (currently available on trunk).

2: C++ Broker uses [Cyrus
SASL](http://freshmeat.net/projects/cyrussasl/) which supports CRAM-MD5
and GSSAPI but these have not been tested yet

### Custom Mechanisms [XXX]

There have been some custom mechanisms added to our implementations.

  --------------- ---------- -----------------
  Component       AMQPLAIN   CRAM-MD5-HASHED
  C++ Broker                  
  C++ Client                  
  Java Broker     M1         M2
  Java Client     M1         M2
  .Net Client                 
  Python Client   M2          
  Ruby Client     M2          
  --------------- ---------- -----------------

  : SASL Custom Mechanisms

#### AMQPLAIN

#### CRAM-MD5-HASHED

The Java SASL implementations require that you have the password of the
user to validate the incoming request. This then means that the user's
password must be stored on disk. For this to be secure either the broker
must encrypt the password file or the need for the password being stored
must be removed.

The CRAM-MD5-HASHED SASL plugin removes the need for the plain text
password to be stored on disk. The mechanism defers all functionality to
the build in CRAM-MD5 module the only change is on the client side where
it generates the hash of the password and uses that value as the
password. This means that the Java Broker only need store the password
hash on the file system. While a one way hash is not very secure
compared to other forms of encryption in environments where the having
the password in plain text is unacceptable this will provide and
additional layer to protect the password. In particular this offers some
protection where the same password may be shared amongst many systems.
It offers no real extra protection against attacks on the broker (the
secret is now the hash rather than the password).
