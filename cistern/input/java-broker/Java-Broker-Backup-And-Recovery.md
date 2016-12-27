# <span class="header-section-number">1</span> Backup And Recovery

# <span class="header-section-number">2</span> Broker

To perform a complete backup whilst the Broker is shutdown, simply copy
all the files the exist beneath `${QPID_WORK}`, assuming all virtualhost
nodes and virtualhost are in their standard location, this will copy all
configuration and persistent message data.

There is currently no safe mechanism to take a complete copy of the
entire Broker whilst it is running.

# <span class="header-section-number">3</span> Virtualhost Node

To perform a complete backup of a Virtualhost node whilst it is stopped
(or Broker down), simply copy all the files the exist beneath
`${QPID_WORK}/<nodename>/config`, assuming the virtualhost node is in
the standard location. This will copy all configuration that belongs to
that virtualhost node.

The technique for backing up a virtualhost node whilst it is running
depends on its type.

## <span class="header-section-number">3.1</span> BDB

Qpid Broker distribution includes the "hot" backup utility `backup.sh`
which can be found at broker bin folder. This utility can perform the
backup when broker is running.

`backup.sh` script invokes
`org.apache.qpid.server.store.berkeleydb.BDBBackup` to do the job.

You can also run this class from command line like in an example below:

java -cp qpid-bdbstore-QPIDCURRENTRELEASE.jar
org.apache.qpid.server.store.berkeleydb.BDBBackup -fromdir
\${QPID\_WORK}/\<nodename\>/config -todir path/to/backup/folder

In the example above BDBBackup utility is called from
qpid-bdbstore-QPIDCURRENTRELEASE.jar to backup the store at
`${QPID_WORK}/<nodename>/config` and copy store logs into
`path/to/backup/folder`.

Linux and Unix users can take advantage of `backup.sh` bash script by
running this script in a similar way.

backup.sh -fromdir \${QPID\_WORK}/\<nodename\>/config -todir
path/to/backup/folder

## <span class="header-section-number">3.2</span> BDB-HA

See ?

## <span class="header-section-number">3.3</span> Derby

Not yet supported

## <span class="header-section-number">3.4</span> JDBC

The responsibility for backup is delegated to the database server
itself. See the documentation accompanying it. Any technique that takes
a consistent snapshot of the database is acceptable.

## <span class="header-section-number">3.5</span> JSON

JSON stores its config in a single text file. It can be safely backed up
using standard command line tools.

# <span class="header-section-number">4</span> Virtualhost

To perform a complete backup of a Virtualhost whilst it is stopped (or
Broker down), simply copy all the files the exist beneath
`${QPID_WORK}/<name>/messages`, assuming the virtualhost is in the
standard location. This will copy all messages that belongs to that
virtualhost.

The technique for backing up a virtualhost whilst it is running depends
on its type.

## <span class="header-section-number">4.1</span> BDB

Use the same backup utility described above, but use the path
`${QPID_WORK}/<name>/messages` instead.

## <span class="header-section-number">4.2</span> Derby

Not yet supported

## <span class="header-section-number">4.3</span> JDBC

The responsibility for backup is delegated to the database server
itself. See the documentation accompanying it. Any technique that takes
a consistent snapshot of the database is acceptable.

## <span class="header-section-number">4.4</span> Provided

The contents of the virtualhost will be backed up as part of virtualhost
node that contains it.

## <span class="header-section-number">4.5</span> BDB-HA

The contents of the virtualhost will be backed up as part of virtualhost
node that contains it.
