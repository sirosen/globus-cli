globus auth
===========

Description
-----------

The Globus Auth service provides tools for managing identities in the Globus
ecosystem.
Identities are primarily represented by a username, typically of the form
``<name>@<domain>``, mapped to an Identity ID, typically a UUID.
Globus Auth guarantees that an Identity ID uniquely identifies a individual,
even in organizations where usernames are reused, so long as the Identity
Provider -- the organization owning the ``<domain>`` portion of the username --
allows access to the correct uniquifying information.

Commands
--------

* :command:`get-identities`

  .. autocli:: globus_cli.services.auth.get_identities

* :command:`token-introspect`

  .. autocli:: globus_cli.services.auth.token_introspect
