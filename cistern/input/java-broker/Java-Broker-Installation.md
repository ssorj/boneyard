# <span class="header-section-number">1</span> Installation

# <span class="header-section-number">2</span> Introduction

This document describes how to install the Java Broker on both Windows
and UNIX platforms.

# <span class="header-section-number">3</span> Prerequisites

## <span class="header-section-number">3.1</span> Java Platform

The Java Broker is an 100% Java implementation and as such it can be
used on any operating system supporting Java 1.7 or higher<span
id="fnref1">[^1^](#fn1)</span>. This includes Linux, Solaris, Mac OS X,
and Windows XP/Vista/7/8.

The broker has been tested with Java implementations from both Oracle
and IBM. Whatever platform you chose, it is recommended that you ensure
it is patched with any critical updates made available from the vendor.

Verify that your JVM is installed properly by following [these
instructions.](#Java-Broker-Miscellaneous-JVM-Verification)

## <span class="header-section-number">3.2</span> Disk

The Java Broker installation requires approximately 20MB of free disk
space.

The Java Broker also requires a working directory. The working directory
is used for the message store, that is, the area of the file-system used
to record persistent messages whilst they are passing through the
Broker. The working directory is also used for the default location of
the log file. The size of the working directory will depend on the how
the Broker is used.

The performance of the file system hosting the work directory is key to
the performance of Broker as a whole. For best performance, choose a
device that has low latency and one that is uncontended by other
applications.

Be aware that there are additional considerations if you are considering
hosting the working directory on NFS.

## <span class="header-section-number">3.3</span> Memory

Qpid caches messages on the heap for performance reasons, so in general,
the Broker will benefit from as much heap as possible. However, on a
32bit JVM, the maximum addressable memory range for a process is 4GB,
after leaving space for the JVM's own use this will give a maximum heap
size of approximately \~3.7GB.

## <span class="header-section-number">3.4</span> Operating System Account

Installation or operation of Qpid does *not* require a privileged
account (i.e. root on UNIX platforms or Administrator on Windows).
However it is suggested that you use an dedicated account (e.g. qpid)
for the installation and operation of the Java Broker.

# <span class="header-section-number">4</span> Download

## <span class="header-section-number">4.1</span> Broker Release

You can download the latest Java broker package from the [Download
Page](&qpidDownloadUrl;).

It is recommended that you confirm the integrity of the download by
verifying the PGP signature matches that available on the site.
Instructions are given on the download page.

# <span class="header-section-number">5</span> Installation on Windows

Firstly, verify that your JVM is installed properly by following [these
instructions.](#Java-Broker-Miscellaneous-JVM-Verification-Windows)

Now chose a directory for Qpid broker installation. This directory will
be used for the Qpid JARs and configuration files. It need not be the
same location as the work directory used for the persistent message
store or the log file (you will choose this location later). For the
remainder this example we will assume that location c:\\qpid has been
chosen.

Next extract the WINDOWSBROKERDOWNLOADFILENAME package into the
directory, using either the zip file handling offered by Windows (right
click the file and select 'Extract All') or a third party tool of your
choice.

The extraction of the broker package will have created a directory
WINDOWSEXTRACTEDBROKERDIRNAME within c:\\qpid

     Directory of c:\qpid\WINDOWSEXTRACTEDBROKERDIRNAME

    07/25/2012  11:22 PM                   .
    09/30/2012  10:51 AM                   ..
    09/30/2012  12:24 AM                   bin
    08/21/2012  11:17 PM                   etc
    07/25/2012  11:22 PM                   lib
    07/20/2012  08:10 PM            65,925 LICENSE
    07/20/2012  08:10 PM             3,858 NOTICE
    07/20/2012  08:10 PM             1,346 README.txt

## <span class="header-section-number">5.1</span> Setting the working directory

Qpid requires a work directory. This directory is used for the default
location of the Qpid log file and is used for the storage of persistent
messages. The work directory can be set on the command-line (for the
lifetime of the command interpreter), but you will normally want to set
the environment variable permanently via the Advanced System Settings in
the Control Panel.

    set QPID_WORK=C:\qpidwork

If the directory referred to by
[QPID\_WORK](#Java-Broker-Appendix-Environment-Variables-Qpid-Work) does
not exist, the Java Broker will attempt to create it on start-up.

# <span class="header-section-number">6</span> Installation on UNIX platforms

Firstly, verify that your JVM is installed properly by following [these
instructions.](#Java-Broker-Miscellaneous-JVM-Verification-Unix)

Now chose a directory for Qpid broker installation. This directory will
be used for the Qpid JARs and configuration files. It need not be the
same location as the work directory used for the persistent message
store or the log file (you will choose this location later). For the
remainder this example we will assume that location /usr/local/qpid has
been chosen.

Next extract the UNIXBROKERDOWNLOADFILENAME package into the directory.

    mkdir /usr/local/qpid
    cd /usr/local/qpid
    tar xvzf UNIXBROKERDOWNLOADFILENAME

The extraction of the broker package will have created a directory
UNIXEXTRACTEDBROKERDIRNAME within /usr/local/qpid

    ls -la UNIXEXTRACTEDBROKERDIRNAME/
    total 152
    drwxr-xr-x   8 qpid  qpid    272 25 Jul 23:22 .
    drwxr-xr-x  45 qpid  qpid   1530 30 Sep 10:51 ..
    -rw-r--r--@  1 qpid  qpid  65925 20 Jul 20:10 LICENSE
    -rw-r--r--@  1 qpid  qpid   3858 20 Jul 20:10 NOTICE
    -rw-r--r--@  1 qpid  qpid   1346 20 Jul 20:10 README.txt
    drwxr-xr-x  10 qpid  qpid    340 30 Sep 00:24 bin
    drwxr-xr-x   9 qpid  qpid    306 21 Aug 23:17 etc
    drwxr-xr-x  34 qpid  qpid   1156 25 Jul 23:22 lib
        

## <span class="header-section-number">6.1</span> Setting the working directory

Qpid requires a work directory. This directory is used for the default
location of the Qpid log file and is used for the storage of persistent
messages. The work directory can be set on the command-line (for the
lifetime of the current shell), but you will normally want to set the
environment variable permanently the user's shell profile file
(\~/.bash\_profile for Bash etc).

    export QPID_WORK=/var/qpidwork
          

If the directory referred to by
[QPID\_WORK](#Java-Broker-Appendix-Environment-Variables-Qpid-Work) does
not exist, the Java Broker will attempt to create it on start-up.

# <span class="header-section-number">7</span> Optional Dependencies

If you wish to utilise storage options using Oracle BDB JE or an
External Database, see ? and ? for details of installing their
dependencies.

------------------------------------------------------------------------

1.  <div id="fn1">

    </div>

    Java Cryptography Extension (JCE) Unlimited Strength required for
    some features[↩](#fnref1)


