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

Message fields:

.. code-block:: bash
  struct HeartBeatMessage {
   1: MessageType messageType = HEART_BEAT,
   2: i64 domino_udid,
   3: i64 seq_no  
  }

.. code-block:: bash

  ./domino-cli.py heartbeat


Interactive CLI mode
====================



Revision: _sha1_

Build date: |today|
