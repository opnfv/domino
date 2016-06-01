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
Make sure that domino-cli.py is in +x mode.

Change directory to where domino-cli.py is located or include file path in the PATH environment variable

* Registration Command

Command line input:

.. code-block:: bash

  ./domino-cli.py register

This message has the following fields that are automatically filled in.

.. code-block:: bash

  Message Type (= REGISTER)
  DESIRED UDID (= if not allocated, this will be assigned as Unique Domino ID)
  Sequence Number (=incremented after each RPC call)
  IP ADDR (= IP address of DOMINO Client to be used by DOMINO Server for future RPC Calls to this client)
  TCP PORT (= TCP port of DOMINO Client to be used by DOMINO Server for future RPC Calls to this client)
  Supported Templates (= Null, this field not used currently)

* Heart Beat Command

Command line input:

.. code-block:: bash

  ./domino-cli.py heartbeat

This message has the following fields that are automatically filled in.

.. code-block:: bash

  Message Type (= HEART_BEAT)
  UDID (= Unique Domino ID assigned during registration)
  Sequence Number (=incremented after each RPC call)

* Label and Template Type Subscription Command

.. code-block:: bash

  ./domino-cli.py subscribe -l <labelname> -t <templatetype>

Note that -l can be substituted by --label and -t can be substituted by --ttype.

To subscribe more than one label or template type, one can repeat the options -l and -t, e.g.:

.. code-block:: bash

  ./domino-cli.py subscribe -l <label1> -l <label2> ... -l <labeln> -t <ttype1> -t <ttype2> ... -t <ttypen>

It is safe to call subscribe command multiple times with duplicate labels.

This message has the following fields that are automatically filled in.

.. code-block:: bash

  Message Type (= SUBSCRIBE)
  UDID (= Unique Domino IDassigned during registration)
  Sequence Number (=incremented after each RPC call)
  Template Operation (= APPEND)
  Label Operation (= APPEND)

The following fields are filled in based on arguments passed on via -l/--label and -t/--ttype flags

.. code-block:: bash

  Supported Template Types 
  Supported Labels

* Template Publishing Command

.. code-block:: bash

  ./domino-cli.py publish -t <toscafile>

Note that -t can be substituted by --tosca-file.

If -t or --tosca-file flag is used multiple times, the last tosca file passed as input will be used. This usage is not recommended as undefined/unintended results may emerge as the Domino client will continue to publish.

This message has the following fields that are automatically filled in.

.. code-block:: bash

  Message Type (= SUBSCRIBE)
  UDID (= Unique Domino IDassigned during registration)
  Sequence Number (=incremented after each RPC call)
  Template Type (= TOSCA)
  Template File

Interactive CLI mode
====================



Revision: _sha1_

Build date: |today|
