# Qpid management tools

## Setup your development environment

    % cd bailey           # Go to the directory containing this README
    % source config.sh    # Setup environment variables
    % install.sh          # Build and install to a checkout-local prefix
    % test.sh             # Run pre-checkin tests

This module depends on Qpid proton and requires python 2.7.

## Command-line tools

All commands take the following options:

    --help
    --user USER
    --password PASSWORD
    --host HOSTNAME
    --port PORT

`qmlist`, `qmquery`, and `qmcall` also take `--node ADDRESS` for
selecting the AMQP management node to direct requests to.

These options may also be specified in the config file at
`$PREFIX/etc/qpid-management/main.conf`.

### qmlist

Enumerate elements of the AMQP management model.

    % qmlist types
    % qmlist attributes
    % qmlist operations
    % qmlist other-nodes

### qmquery

Query for AMQP entities.  At the moment, the functionality here is
very basic.

    % qmquery

### qmcall

Invoke operations on AMQP entities.

    % qmcall org.amqp.management READ self

### qmtest

Run protocol conformance tests.

    # Run against an external management server
    % qmtest

    # Run against the built-in mock server
    % qmtest --self

### Planned tools

 - qmping
 - qmcreate, qmread, qmupdate, qmdelete
 - qmtop

## Python management API

This is the API used internally by the command-line tools and tests.
It implements the AMQP Management request-response protocol and
provides high-level management functions.  All messaging operations
are synchronous.

To use, import from `qpid_management`.  The API is contained in the
following files:

    python/qpid_management/model.py
    python/qpid_management/session.py

## Mock management server

A server implementation is provided for self tests.  This is used by
`qmtest --self`.

    python/qpid_management_internal/test/server.py

## Development utilities

### qpid-java-broker

This is a script to operate the java broker in a unixy way.  Use
`qpid-java-broker --help` to see what it offers.  By default it looks
for the broker code under `/opt/qpid-java-broker`.  You can override
it by setting the `QPID_HOME` variable in your environment.

For my development environment, I like to put a symlink from
`/opt/qpid-java-broker` to the place where I keep the qpid java build
output:

    % sudo ln -s ~/code/qpid/java/build /opt/qpid-java-broker
