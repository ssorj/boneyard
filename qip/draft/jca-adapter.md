[Index](../index.html)

# JCA adapter for Qpid

## Status

Draft

## Summary

Implement a JCA adapter for Qpid

## Problem

Currently there is no way to integrate the use of Qpid messaging into
a Java Application Server.

## Solution

The solution is to create a JCA (J2EE Connector Architecture) adapter
to allow the Qpid JMS client to correctly work with the J2EE
container.

## Implementation Notes

This is an entirely new Java component, but may require small amounts
of change to the JMS client code.

The current plan is to incorporate the new JCA code in a self
contained directory of "qpid/java" either "jca" or "ra". The adapter
code changes will aim to be minimally invasive into the existing JMS
client, and will also use JMS specified interfaces where ever possible
so that the adapter isn't tightly coupled to the JMS client.  So that
maintaining the JMS client won't break the JCA adapter needlessly.

Ideally we will enshrine a small interface used by the JCA adapter
that will remain stable under further JMS client maintenance.

Currently I'm working from existing Apache licensed code (The HornetQ
JCA Adapter) which should have minimal relicensing issues.

## Consequences

There are some implications for various areas:

__Development:__ Assuming there will be a well defined interface that
the adapter uses then other Java development will be minimally
affected.

__Release:__ The JCA adapter will need to build a new release artifact
which will need to be released possibly together with the JMS client,
possibly independently.

## Contributor-in-Charge

Andrew Stitcher, <astitcher@apache.org>

## Version

1.0
