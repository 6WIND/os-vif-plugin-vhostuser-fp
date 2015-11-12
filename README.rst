==================
vif_plug_vhostuser
==================

An `os-vif` VIF plugin for plugging and unplugging virtual interfaces that use
the QEMU vhost-user feature for efficient virtio-net I/O for data plane
communication between host and guest.

Features
--------

* A `vif_plug_vhostuser.vhostuser.VhostuserPlugin` VIF plugin that uses the
  QEMU vhost-user virtio-net I/O features.

Installation
------------

Install the OVS VIF plugins using `pip`::

    sudo pip install vif_plug_vhostuser

After doing so, the `os-vif` library's `initialize()` method will automatically
load both of the OVS VIF plugins in this library and allow Nova and any other
system to plug VIFs that use OpenVSwitch bridges in some capacity.

Configuration
-------------

The following configuration options are used by the
`vif_plug_ovs.ovs_hybrid.OvsHybridPlugin` VIF plugin and are passed from the
`os_vif.initialize(**config)` function:

* `network_device_mtu` -- Defaults to `1500`. Override to set the max
  transmission unit for the bridge that is created to house iptables rules.
* `use_ipv6` -- Defaults to `False`. Override to enable IPv6 iptables rules on
  the bridge created by the plugin.
* `iptables_top_regex` -- Defaults to `''`.
* `iptables_bottom_regex` -- Defaults to `''`.
* `iptables_drop_action` -- Defaults to `'DROP'`.
* `forward_bridge_interface` -- Defaults to `['all']`.
* `disable_rootwrap` -- Defaults to `False`. Override to entirely disable any
  use of rootwrap and instead rely solely on sudoers files.
* `use_rootwrap_daemon` -- Defaults to `False`. Override to enable the rootwrap
  daemon mode which can increase the performance of root-run commands.
* `rootwrap_config` -- Defaults to `'/etc/nova/rootwrap.conf'`. Path to the
  `oslo.rootwap` config file.
* `ovs_vsctl_timeout` -- Defaults to `120`. Number of seconds the `ovs-vsctl`
  program should wait before erroring out.
