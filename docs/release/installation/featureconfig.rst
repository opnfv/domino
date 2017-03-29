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
Domino Configuration
====================
Domino Server and Clients can be configured via (i) passing command line options
(see API documentation) and (ii) the configuration file "domino_conf.py" under the
main directory.

* The default file for logging is set as none and log level set as "WARNING".

Domino Server
-------------
* The default server unique user ID is set as 0 in the configuration file.

* The default TCP port for RPC calls is set as 9090 in the configuration file.

* The default database file for Domino Server is set as "dominoserver.db" under the main directory

* The default folder for keeping published TOSCA files and pushed parts is set as "toscafiles" in the configuration file via variable TOSCADIR.

* The default log level (WARNING) can be changed by passing the flags --log or -l followed by a log level, e.g., ERROR, WARNING, INFO, or DEBUG.

Domino Client
-------------
* The default mode of CLI is non-interactive (i.e., Domino CLI Utility is used). Passing --iac=TRUE would begin the client in interactive mode.

* The default log level (WARNING) can be changed by passing the flags --log or -l followed by a log level, e.g., ERROR, WARNING, INFO, or DEBUG.

* The default Domino Server IP is set as "localhost". This can be overwritten at the time of launching DominoClient via the option flags -i or --ipaddr followed by the IP address of the actual server hosting the Domino Server.

* The default Domino Client TCP port for RPC calls is set as 9091 in the configuration file. It can be overwritten when the DominoClient is launched by passing the flags --port or -p followed by the port number.

* The default folder for keeping preceived TOSCA files is set as "toscafiles" in the configuration file via variable TOSCA_RX_DIR.

