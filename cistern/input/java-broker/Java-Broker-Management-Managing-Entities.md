# <span class="header-section-number">1</span> Managing Entities

This section describes how to manage entities within the Broker. The
principles underlying entity management are the same regardless of
entity type. For this reason, this section begins with a general
description that applies to all.

Since not all channels support the management of all entity type, this
section commences with a table showing which entity type is supported by
each channel.

# <span class="header-section-number">2</span> General Description

The following description applies to all entities within the Broker
regardless of their type.

-   All entities have a parent, and may have children. The parent of the
    Broker is called the System Context. It has no parent.

-   Entities have one or more attributes. For example a `name`, an `id`
    or a `maximumQueueDepth`

-   Entities can be durable or non-durable. Durable entities survive a
    restart. Non-durable entities will not.

-   Attributes may have a default value. If an attribute value is not
    specified the default value is used.

-   Attributes values can be expressed as a simple value (e.g. `myName`
    or `1234`), in terms of context variables (e.g.`${foo}` or
    `/data/${foo}/`).

-   Each entity has zero or more context variables.

-   The System Context entity (the ultimate ancestor of all object) has
    a context too. It is read only and is populated with all Java System
    Properties. Thus it can be influenced from the Broker's external
    environment. See
    [QPID\_OPTS](#Java-Broker-Appendix-Environment-Variables-Qpid-Opts)
    environment variable.

-   When resolving an attribute's value, if the value contains a
    variable (e.g.`${foo}`), the variable is first resolved using the
    entity's own context variables. If the entity has no definition for
    the context variable, the entity's parent is tried, then its
    grandparent and so forth, all the way until the SystemContext is
    reached.

-   Some entities support state and have a lifecycle.

What follows now is a section dedicated to each entity type. For each
entity type key features are described along with the entities key
attributes, key context variables, details of the entities lifecycle and
any other operations.
