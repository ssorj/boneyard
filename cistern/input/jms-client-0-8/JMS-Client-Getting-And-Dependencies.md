# <span class="header-section-number">1</span> Getting the Client And Dependencies

# <span class="header-section-number">2</span> Getting the Client

The Qpid JMS client is available as a bundle or from QPIDMAVENREPODESC.

The bundle (a .tar.gz) includes the Qpid JMS client itself (formed by
two JAR: qpid-client and qpid-common) together with slf4j-api, and
geronimo-jms\_1.1\_spec. There is also a qpid-all JAR artifact that, for
convenience, includes a manifest classpath that references the other
JARs. The bundle is available from
[QPIDDOWNLOADURLDESC](&qpidDownloadUrl;).

The Qpid JMS client is also available from QPIDMAVENREPODESC. Add the
following dependency:

        <dependency>
          <groupId></groupId>
          <artifactId></artifactId>
          <version></version>
        </dependency>
        

? illustrates a minimal Maven POM required to use the Qpid Client.

# <span class="header-section-number">3</span> Dependencies

The Qpid JMS client has minimal set of external dependencies.

It requires:

-   JDK 1.7 or higher.

-   JMS 1.1 specification (such as geronimo-jms\_1.1\_spec JAR)

-   [Apache SLF4J](http://www.slf4j.org) (slf4j-api-x.y.z JAR)

The use of SLF4J means that application authors are free to plug in any
logging framework for which an SLF4J binding exists.
