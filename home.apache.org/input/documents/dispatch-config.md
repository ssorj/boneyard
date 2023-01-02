# Dispatch configuration proposal

Updated 12 May 2016.

## Related material

 - <https://github.com/apache/qpid-dispatch/blob/master/etc/qdrouterd.conf>
 - <https://github.com/apache/qpid-dispatch/blob/master/tests/policy-2/test-router-with-policy.json.in>
 - <http://qpid.apache.org/releases/qpid-dispatch-master/man/qdrouterd.conf.html>

## Questions and issues

 - What is displayNameFile for?  Should that be part of the *router*
   config?  What is the user supposed to do with it?
 - qdrouterd.conf has "router.config.address" as a heading instead of
   "address".  Intentional?
 - Console is presented as a section with no properties.
 - Should we remove password?
 - qdrouterd.conf has "ssl-profile" in an example

## Proposed changes

### General

 - Don't use routerId or addr in example configs
 - idleTimeoutSeconds -> idleTimeout - Document the unit but don't put
   it in the name, same as helloInterval, helloMaxAge, raInterval
 - dir -> direction - To avoid collision with directory
 - Use a standard list syntax throughout and document it in
   qdrouterd.conf man page
 - Describe comment syntax in qdrouterd.conf man page
 - Consider removing password
 - saslConfigPath -> saslConfigFile - Matching certFile, keyFile,
   passwordFile, displayNameFile
 - debugDump -> debugFile

### Policy

 - Remove the standalone "policy" block; move its attributes to router
 - Replace policyRuleset with vhost
 - Locate group policy attributes with the group definition
 - Consider allowRemoteHosts (taking ips and ip ranges) instead of the
   host group business

## Minimal example

        router {
            id: router1
        }

        listener {
            # According to the docs, no properties are necessary here
        }

## Policy example

        router {
            id: router1
            enablePolicy: true
            maxConnections: 10
        }

        listener {
            host: 127.0.0.1
        }

        vhost {
            name: alpha.example.com
            maxConnections: 12
            allowUnknownUser: true
            groups {
                admin {
                    users: alice, adam
                    maxFrameSize: 3
                    allowRemoteHosts: 10.0.0.1, 10.0.0.11
                    allowSources: a, b
                    allowTargets: x, y
                }
                other {
                    users: bob, george
                    maxSessions: 12
                    allowRemoteHosts: 0.0.0.0
                    allowAnonymousSender: true
                }
            }
        }

## Annotated example (incomplete)

        router {
            id: router1                  # Required and no default
            # mode: standalone           # Required: standalone or interior
            # saslConfigName: qdrouterd
            # saslConfigFile: [path]
            # debugFile:
            # workerThreads: 4
            # helloInterval: 1
            # helloMaxAge: 3
            # raInterval: 30
            # raIntervalFlux: 4
        }

        listener {
            # host: 127.0.0.1
            # port: amqp
            # protocolFamily: [computed] # IPv4, IPv6, or none
            # role: normal               # normal, inter-outer, on-demand
            # authenticatePeer:          # What is the default?
            # certDb:
            # certFile:
            # keyFile:
            # passwordFile:
            # password:
        }
