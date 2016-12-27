# Security

[Up to Index](index.html)

 - [Authentication](authentication.html)
 - [Authorization](authorization.html)
    - [ACL syntax](acl-syntax.html)
 - [Quotas](quotas.html)
 - [SSL](ssl.html)

This chapter describes how authentication, rule-based authorization,
encryption, and digital signing can be accomplished using Qpid.
Authentication is the process of verifying the identity of a user; in
Qpid, this is done using the SASL framework. Rule-based authorization is
a mechanism for specifying the actions that each user is allowed to
perform; in Qpid, this is done using an Access Control List (ACL) that
is part of the Qpid broker. Encryption is used to ensure that data is
not transferred in a plain-text format that could be intercepted and
read. Digital signatures provide proof that a given message was sent by
a known sender. Encryption and signing are done using SSL (they can also
be done using SASL, but SSL provides stronger encryption).
