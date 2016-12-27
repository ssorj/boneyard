# SSL

Encryption and certificate management for `qpidd` is provided by
Mozilla's Network Security Services Library (NSS).

1. You will need a certificate that has been signed by a Certification
   Authority (CA). This certificate will also need to be trusted by
   your client. If you require client authentication in addition to
   server authentication, the client's certificate will also need to
   be signed by a CA and trusted by the broker.

   In the broker, SSL is provided through the `ssl.so` module. This
   module is installed and loaded by default in Qpid. To enable the
   module, you need to specify the location of the database containing
   the certificate and key to use. This is done using the
   `ssl-cert-db` option.

   The certificate database is created and managed by the Mozilla
   Network Security Services (NSS) `certutil` tool. Information on
   this utility can be found on the
   [Mozilla website](http://www.mozilla.org/projects/security/pki/nss/tools/certutil.html),
   including tutorials on setting up and testing SSL connections. The
   certificate database will generally be password protected. The
   safest way to specify the password is to place it in a protected
   file, use the password file when creating the database, and specify
   the password file with the `ssl-cert-password-file` option when
   starting the broker.

   The following script shows how to create a certificate database
   using certutil:

        $ mkdir ${CERT_DIR}
        $ certutil -N -d ${CERT_DIR} -f ${CERT_PW_FILE}
        $ certutil -S -d ${CERT_DIR} -n ${NICKNAME} -s "CN=${NICKNAME}" -t "CT,," -x -f ${CERT_PW_FILE} -z /usr/bin/certutil

   When starting the broker, set `ssl-cert-password-file` to the value
   of `${CERT_PW_FILE}`, set `ssl-cert-db` to the value of
   `${CERT_DIR}`, and set `ssl-cert-name` to the value of
   `${NICKNAME}`.

2. The following SSL options can be used when starting the broker:

    `--ssl-use-export-policy`
    :   Use NSS export policy

    `--ssl-cert-password-file `
    :   Required. Plain-text file containing password to use for
        accessing certificate database.

    `--ssl-cert-db `
    :   Required. Path to directory containing certificate database.

    `--ssl-cert-name `
    :   Name of the certificate to use. Default is
        `localhost.localdomain`.

    `--ssl-port `
    :   Port on which to listen for SSL connections. If no port is
        specified, port 5671 is used.

    `--ssl-require-client-authentication`
    :   Require SSL client authentication (i.e. verification of a client
        certificate) during the SSL handshake. This occurs before SASL
        authentication, and is independent of SASL.

        This option enables the `EXTERNAL` SASL mechanism for SSL
        connections. If the client chooses the `EXTERNAL` mechanism, the
        client's identity is taken from the validated SSL certificate,
        using the `CN`literal\>, and appending any `DC`literal\>s to
        create the domain. For instance, if the certificate contains the
        properties `CN=bob`, `DC=acme`, `DC=com`, the client's identity
        is `bob@acme.com`.

        If the client chooses a different SASL mechanism, the identity
        take from the client certificate will be replaced by that
        negotiated during the SASL handshake.

    `--ssl-sasl-no-dict`
    :   Do not accept SASL mechanisms that can be compromised by
        dictionary attacks. This prevents a weaker mechanism being
        selected instead of `EXTERNAL`, which is not vulnerable to
        dictionary attacks.

   Also relevant is the `--require-encryption` broker option. This will
   cause `qpidd` to only accept encrypted connections.

C++ clients:
:   1.  In C++ clients, SSL is implemented in the `sslconnector.so`
        module. This module is installed and loaded by default in Qpid.

        The following options can be specified for C++ clients using
        environment variables:

          SSL Client Options for C++ clients
          ------------------------------------ ----------------------------------------------------------------------------------------------------------------------------
          `QPID_SSL_USE_EXPORT_POLICY`         Use NSS export policy
          `QPID_SSL_CERT_PASSWORD_FILE `       File containing password to use for accessing certificate database
          `QPID_SSL_CERT_DB `                  Path to directory containing certificate database
          `QPID_SSL_CERT_NAME `                Name of the certificate to use. When SSL client authentication is enabled, a certificate name should normally be provided.

          : SSL Client Environment Variables for C++ clients

    2.  When using SSL connections, clients must specify the location of
        the certificate database, a directory that contains the client's
        certificate and the public key of the Certificate Authority.
        This can be done by setting the environment variable
        `QPID_SSL_CERT_DB` to the full pathname of the directory. If a
        connection uses SSL client authentication, the client's password
        is also needed—the password should be placed in a protected
        file, and the `QPID_SSL_CERT_PASSWORD_FILE` variable should be
        set to the location of the file containing this password.

    3.  To open an SSL enabled connection in the Qpid Messaging API, set
        the `protocol` connection option to `ssl`.

Java clients:
:   1.  For both server and client authentication, import the trusted CA
        to your trust store and keystore and generate keys for them.
        Create a certificate request using the generated keys and then
        create a certificate using the request. You can then import the
        signed certificate into your keystore. Pass the following
        arguments to the Java JVM when starting your client:

            -Djavax.net.ssl.keyStore=/home/bob/ssl_test/keystore.jks
            -Djavax.net.ssl.keyStorePassword=password
            -Djavax.net.ssl.trustStore=/home/bob/ssl_test/certstore.jks
            -Djavax.net.ssl.trustStorePassword=password

    2.  For server side authentication only, import the trusted CA to
        your trust store and pass the following arguments to the Java
        JVM when starting your client:

            -Djavax.net.ssl.trustStore=/home/bob/ssl_test/certstore.jks
            -Djavax.net.ssl.trustStorePassword=password

    3.  Java clients must use the SSL option in the connection URL to
        enable SSL encryption, e.g.

            amqp://username:password@clientid/test?brokerlist='tcp://localhost:5672?ssl='true''

    4.  If you need to debug problems in an SSL connection, enable
        Java's SSL debugging by passing the argument
        `-Djavax.net.debug=ssl` to the Java JVM when starting your
        client.
