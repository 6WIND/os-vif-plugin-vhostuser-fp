====================
Enabling in Devstack
====================

1. Download DevStack::

      git clone https://git.openstack.org/openstack-dev/devstack
      cd devstack

3. Add this repo as an external repository::

      > cat local.conf
      [[local|localrc]]
      enable_plugin os-vif-plugin-vhostuser-fp https://github.com/6WIND/os-vif-plugin-vhostuser-fp

4. Enable 6WIND os-vif plugin for fastpath vhostuser support::

      enable_service os-vif-fp-plugin

6. Run ``stack.sh``.
