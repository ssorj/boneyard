[Index](../index.html)

# Qpid Improvement Process

## Status

Draft

## Summary

A model for describing Qpid improvements and a process to approve them
for new Qpid releases.

## Problem

 - Qpid brings together people from different places and disciplines.
 - Qpid has many components, and they interact.
 - Qpid is changing all the time.

A Qpid release requires careful planning and coordination.
Developers, writers, and testers need to know what's coming, what it
does, and who is affected.

If we don't communicate, we will fail to deliver high-quality
releases.

## Solution

Introduce a standard process for proposing and accepting major changes
in a Qpid release.  The centerpiece of this process is a document
called a Qpid Improvement Proposal (QIP, pronounced "quip") that
answers questions about the purpose and impact of a new feature or
other significant change.

The document has three main functions:

 - To describe the scope and importance of a new feature or change, so
   the Qpid community can judge whether to include it in a new
   release.
 - To explain to impacted parties what the consequences of the change
   are, so the Qpid community can better coordinate.
 - To serve as high-level design documentation, so the Qpid community
   can reference and evaluate its choices.

Any Qpid contributor can submit a QIP to the community for approval.
A Qpid release plan must include a deadline for QIP submission and
another deadline to approve, reject, or defer the QIPs for the
upcoming release.

QIPs live in Qpid source control.  Once a QIP is declared final, it
should undergo only minor changes to correct or clarify its content.

A QIP will typically be used to propose new features, but it can also
be used to propose any other kind of change that impacts a Qpid
release.  For instance, a QIP may describe a change to a community
process, as this QIP does.

Smaller changes such as bug fixes or extensions of largely established
functionality do not require a QIP.

## Rationale

We in the Qpid community haven't always maintained the lines of
communication necessary to deliver quality releases in a timely way.
That's in part because we haven't had enough visibility into what
changes are landing.

Our ticketing system, Jira, offers the potential to have visibility
and control of major changes.  It is, however, not sufficient by
itself.  A QIP is designed to ask the questions we need answered in
order to manage releases at a higher level, to set a broad direction.

The lifecycle of a Jira is not like that of a QIP.  Whereas a Jira is
normally resolved and forgotten, a completed QIP becomes a permanent
part of the history and documentation of Qpid.

Other community projects such as Python and Gnome have used a process
like this one, and it's well liked by contributors and users.

## Implementation Notes

1. Publish the draft process for discussion on the Qpid dev list.
2. Incorporate changes from comments.
3. Use the new process on an optional basis during the 0.10 release.
4. After further revision, vote on whether the new process should be
   adopted for future releases.

## Consequences

This new process changes the way Qpid plans new releases.  As a
result, it impacts every Qpid contributor.

## References

 - [QIP Template](../qip-template.html) with a description of each field
 - [Notes](../notes.html)

## Contributor-in-Charge

Justin Ross, <jross@redhat.com>

## Version

0.0
