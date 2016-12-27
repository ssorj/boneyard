# Replicating Queues with the HA module

As well as support for an active-passive cluster, the `HA` module allows
you to replicate individual queues, even if the brokers are not in a
cluster. The original queue is used as normal. The replica queue is
updated automatically as messages are added to or removed from the
original queue.

> **Warning**
>
> It is not safe to modify the replica queue other than via the
> automatic updates from the original. Adding or removing messages on
> the replica queue will make replication inconsistent and may cause
> message loss. The `HA` module does *not* enforce restricted access to
> the replica queue (as it does in the case of a cluster) so it is up to
> the application to ensure the replica is not used until it has been
> disconnected from the original.

## Replicating queues

To create a replica queue, the `HA` module must be loaded on both the
original and replica brokers (it is loaded by default.) You also need to
set the configuration option:

        ha-queue-replication=yes
          

to enable this feature on a stand-alone broker. It is automatically
enabled for brokers that are part of a cluster.

Suppose that `myqueue` is a queue on `node1` and we want to create a
replica of `myqueue` on `node2` (where both brokers are using the
default AMQP port.) This is accomplished by the command:

        qpid-config --broker=node2 add queue --start-replica node1 myqueue
          

If `myqueue` already exists on the replica broker you can start
replication from the original queue like this:

        qpid-ha replicate -b node2 node1 myqueue
          

## Replicating queues between clusters

You can replicate queues between two standalone brokers, between a
standalone broker and a cluster, or between two clusters (see ?.) For
failover in a cluster there are two cases to consider.

1.  When the *original* queue is on the active node of a cluster,
    failover is automatic. If the active node fails, the replication
    link will automatically reconnect and the replica will continue to
    be updated from the new primary.

2.  When the *replica* queue is on the active node of a cluster, there
    is no automatic failover. However you can use the following
    workaround.

### Work around for fail-over of replica queue in a cluster

When a primary broker fails the cluster resource manager calls a script
to promote a backup broker to be the new primary. By default this script
is `/etc/init.d/qpidd-primary` but you can modify that in your
`cluster.conf` file (see ?.)

You can modify this script (on each host in your cluster) by adding
commands to create your replica queues just before the broker is
promoted, as indicated in the following exceprt from the script:

    start() {
        service qpidd start
        echo -n $"Promoting qpid daemon to cluster primary: "
        ################################
        #### Add your commands here ####
        ################################
        $QPID_HA -b localhost:$QPID_PORT promote
        [ "$?" -eq 0 ] && success || failure
    }
        

Your commands will be run, and your replicas created, whenever the
system fails over to a new primary.
