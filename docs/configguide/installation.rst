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
Domino Installation
===================

Note: The steps below are tested for Ubuntu (16.04, 14.04) and OS X El Capitan.

Prerequisites
-------------
* git
* python-pip
* python (version =2.7)
* tosca-parser (version >=0.4.0)
* heat-translator (version >=0.5.0)

Installation Steps (Single Node)
--------------------------------

* Step-0: Prepare Environment

.. code-block:: bash

  > $sudo pip install tosca-parser
  > $sudo pip install heat-translator
  > $sudo pip install requests

* Step-1: Get the Domino code

.. code-block:: bash

  > $git clone https://gerrit.opnfv.org/gerrit/domino

* Step-2: Go to the main domino directory

.. code-block:: bash

  > cd domino

You should see DominoClient.py, DominoServer.py, and domino-cli.py as executibles.

Installation Steps (Multiple Node)
----------------------------------

Repeat the installation steps for single node on each of the nodes. The script
run_multinode.sh under ./domino/tests directory deploys the Domino Code on three
hosts from a deployment node and tests RPC calls.
