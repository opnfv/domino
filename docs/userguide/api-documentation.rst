.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

.. image:: ../etc/opnfv-logo.png 
  :height: 40
  :width: 200
  :alt: OPNFV
  :align: left
.. these two pipes are to seperate the logo from the first title
|
|
Using domino-cli Client
=======================

* heartbeat message

Command line input:

.. code-block:: bash

  ./domino-cli.py heartbeat

This message has the following fields that are automatically filled in.

.. code-block:: bash

  Message Type (= HEART_BEAT)
  UDID (= assigned during registration)
  Sequence Number (=incremented after each RPC call)

Interactive CLI mode
====================



Revision: _sha1_

Build date: |today|
