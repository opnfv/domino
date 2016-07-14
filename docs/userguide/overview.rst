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
Domino Overview
===============
Domino provides a distribution service for Network Service (NS) and Virtual
Network Function (VNF) descriptors. It is targeted towards supporting many
network controllers, service orchestrators, VNF managers, Operation and
Business Support Systems. Producers of Network Service Descriptors (NSDs)
and VNF Descriptors (VNFD) use Domino Service as an entry point to publish
these descriptors. Currently Domino only supports Tosca Simple Profile for
Network Functions Virtualization (http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/tosca-nfv-v1.0.html) as the data model for NSDs and VNFDs.

Orchestrators, controllers, and managers use Domino service to announce their
capabilities in the form of policy labels. For instance a Virtual Infrastructure
Manager (VIM) that is capable of performing an affinity based VNF or VDU
placement can specify a label in the form "tosca.policies.Placement.affinity"
and subscribe Domino to be able to host VNFs or VDUs requesting such a placement policy.
