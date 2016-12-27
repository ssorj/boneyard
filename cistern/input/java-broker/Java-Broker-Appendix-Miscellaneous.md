# <span class="header-section-number">1</span> Miscellaneous

# <span class="header-section-number">2</span> JVM Installation verification

## <span class="header-section-number">2.1</span> Verify JVM on Windows

Firstly confirm that the JAVA\_HOME environment variable is set
correctly by typing the following at the command prompt:

    echo %JAVA_HOME%

If JAVA\_HOME is set you will see something similar to the following:

    c:"\PROGRA~1"\Java\jdk1.7.0_60\
          

Then confirm that a Java installation (1.7 or higher) is available:

    java -version

If java is available on the path, output similar to the following will
be seen:

    java version "1.7.0_60"
    Java(TM) SE Runtime Environment (build 1.7.0_60-b19)
    Java HotSpot(TM) 64-Bit Server VM (build 24.60-b09, mixed mode)

## <span class="header-section-number">2.2</span> Verify JVM on Unix

Firstly confirm that the JAVA\_HOME environment variable is set
correctly by typing the following at the command prompt:

    echo $JAVA_HOME

If JAVA\_HOME is set you will see something similar to the following:

    /usr/java/jdk1.7.0_60
          

Then confirm that a Java installation (1.7 or higher) is available:

    java -version

If java is available on the path, output similar to the following will
be seen:

    java version "1.7.0_60"
    Java(TM) SE Runtime Environment (build 1.7.0_60-b19)
    Java HotSpot(TM) 64-Bit Server VM (build 24.60-b09, mixed mode)

# <span class="header-section-number">3</span> Installing External JDBC Driver

In order to use a JDBC Virtualhost Node or a JDBC Virtualhost, you must
make the Database's JDBC 4.0 compatible drivers available on the
Broker's classpath. To do this copy the driver's JAR file into the
`${QPID_HOME}/lib/opt` folder.

    Unix:
    cp driver.jar qpid-broker-QPIDCURRENTRELEASE/lib/opt

    Windows:
    copy driver.jar qpid-broker-QPIDCURRENTRELEASE\lib\opt

# <span class="header-section-number">4</span> Installing Oracle BDB JE

The Oracle BDB JE is not distributed with Apache Qpid owing to license
considerations..

If you wish to use a BDB Virtualhost Node, BDB Virtualhost, or BDB HA
Virtualhost Node you must make the BDB JE's JAR available on the
Broker's classpath.

Download the Oracle BDB JE ORACLEBDBPRODUCTVERSION release [from the
Oracle website.](&oracleJeDownloadUrl;)

The download has a name in the form je-ORACLEBDBPRODUCTVERSION.tar.gz.
It is recommended that you confirm the integrity of the download by
verifying the MD5.

Copy the je-ORACLEBDBPRODUCTVERSION.jar from within the release into
`${QPID_HOME}/lib/opt` folder.

    Unix:
    cp je-ORACLEBDBPRODUCTVERSION.jar qpid-broker-QPIDCURRENTRELEASE/lib/opt

    Windows:
    copy je-ORACLEBDBPRODUCTVERSION.jar qpid-broker-QPIDCURRENTRELEASE\lib\opt
