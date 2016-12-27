# <span class="header-section-number">1</span> Minimal Maven POM

The following is a minimal Maven POM required to use the Qpid Client. It
is suitable for use with the [examples](#JMS-Client-0-8-Examples)
included in this book.

        
    <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
      <modelVersion>4.0.0</modelVersion>
      <groupId>test</groupId>
      <artifactId>test</artifactId>
      <version>0.0.1-SNAPSHOT</version>
      <dependencies>
        <dependency>
          <groupId></groupId>
          <artifactId></artifactId>
          <version></version>
        </dependency>
        <dependency>
          <groupId>org.slf4j</groupId>
          <artifactId>slf4j-log4j12</artifactId>
          <version>1.6.4</version>
        </dependency>
        <dependency>
          <groupId>org.apache.geronimo.specs</groupId>
          <artifactId>geronimo-jms_1.1_spec</artifactId>
          <version>1.1.1</version>
        </dependency>
      </dependencies>
    </project>
        
      

Note: We use the SLF4J Binding for Log4J12 here, but any SLF4J Binding
could be used instead. Similarly, Geronimo JMS Spec is used, but any
dependency that provides the JMS 1.1 specification could be subsituted.
