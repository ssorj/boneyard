# Proton API layout

## Overview

| Namespace                  | Content                                       | Depends on                   |
|----------------------------|-----------------------------------------------|------------------------------|
| [proton/amqp][1]           | AMQP data encoding and decoding               | proton/internal if needed    |
| [proton or proton/core][2] | AMQP model, event processing, error handling  | proton/amqp                  |
| [proton/messenger][3]      | Home of the Messenger API                     | proton or proton/core        |
| [proton/internal][4]       | API internals and language extensions         | -                            |

[1]: #namespace-protonamqp
[2]: #namespace-protoncore-or-proton
[3]: #namespace-protonmessenger
[4]: #namespace-protoninternal

## Entity names

The entity names in this document take the form 'some-entity', lower
case and hyphenated.  Implementers are meant to translate them into
language-conventional variants.

 - value remains `value` or becomes `Value`
 - event-type becomes `event_type` or `EventType`
 - url-error becomes `url_error` or `UrlError`

## Root namespace

In general, prefer simply 'proton' as the root namespace.  If your
language uses fully qualified package names a la Java, it should
include 'qpid', as in org.apache.qpid.proton.

## Namespace 'proton/amqp'

AMQP data encoding and decoding.  These are available to the user but
won't typically be necessary for the user to import when building a
Proton-based application.

### AMQP data types

These names must reflect the type names in the AMQP specification.
Because they are prone to collisions with language keywords, they must
the carry the "amqp" prefix.

<div class="four-column" markdown="1">

 - amqp-binary
 - amqp-boolean
 - amqp-null
 - amqp-ubyte
 - amqp-ushort
 - amqp-uint
 - amqp-ulong
 - amqp-byte
 - amqp-short
 - amqp-int
 - amqp-long
 - amqp-float
 - amqp-double
 - amqp-decimal32
 - amqp-decimal64
 - amqp-decimal128
 - amqp-char
 - amqp-timestamp
 - amqp-uuid
 - amqp-string
 - amqp-symbol
 - amqp-list
 - amqp-map

</div>

### Encode and decode utilities

<div class="two-column" markdown="1">

 - data
 - value
 - value-type
 - decoder
 - decode-error or -exception
 - encoder
 - encode-error or -exception

</div>

## Namespace 'proton' or 'proton/core'

This is the primary user entry point for the event-driven API.  Most
example programs will import only this namespace.

### AMQP model entities

<div class="four-column" markdown="1">

 - endpoint
 - container
 - connection
 - session
 - session-error or -exception
 - link
 - receiver
 - sender
 - terminus
 - condition
 - delivery
 - delivery-state
 - address
 - message

</div>

### Event processing

<div class="four-column" markdown="1">

 - event
 - event-type
 - collector
 - reactor
 - acceptor
 - timer
 - task
 - selectable
 - general-handler
 - outgoing-message-handler
 - incoming-message-handler
 - transaction-handler
 - transactional-client-handler

</div>

### Transport entities

<div class="two-column" markdown="1">

 - transport
 - transport-error or -exception
 - ssl
 - ssl-domain
 - ssl-error or -exception
 - sasl

</div>

### Error handling
 
 - proton-error or proton-exception
 - timeout-error or -exception

### Important utilities

These are utilities that don't fit any other category here but feature
prominently in common code such as examples.

 - duration
 - url
 - url-error or -exception

## Namespace 'proton/messenger'

A home for the Messenger API.

 - messenger
 - messenger-error or -exception
 - tracker
 - subscription

## Namespace 'proton/internal'

A place for anything that you happen to need in your implementation,
but which you don't wish to advertise as central to the API.

 - API internals that will find infrequent use
 - Language extensions
