globus transfer
===============

Description
-----------

The *Globus Transfer* service provides tools for managing **Endpoints**,
data on **Endpoint** filesystems, long-running Transfer and Delete **Tasks**,
**Shares**, and Access to these resources.

A Globus **Endpoint** is a representation of a filesystem, usually connected to
the service via a GridFTP server running in *Globus Connect Personal* or
*Globus Connect Server*.
**Endpoints** allow *Globus Transfer* to manage long-running Tasks, control
access to the filesystem (via **Shared Endpoints** or "**Shares**"), and to
directly access the filesystem for ``ls``, ``mkdir``, and ``rename``
operations.

Commands
--------

* ``endpoint``

  : Manage Globus Endpoint definitions

* ``task``
  
  : Manage asynchronous Tasks

* ``acl``
  
  : Manage Endpoint Access Control Lists

* ``bookmark``
  
  : Manage Endpoint Bookmarks

* ``async-transfer``

  .. autocli:: globus_cli.services.transfer.submit_transfer

* ``async-delete``

  .. autocli:: globus_cli.services.transfer.submit_delete

* ``ls``

  .. autocli:: globus_cli.services.transfer.op_ls

* ``mkdir``

  .. autocli:: globus_cli.services.transfer.op_mkdir

* ``rename``

  .. autocli:: globus_cli.services.transfer.op_rename
