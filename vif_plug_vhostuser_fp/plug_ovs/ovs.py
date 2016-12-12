#    Copyright 2016 6WIND S.A.
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging

from os_vif_plugin_vhostuser_fp import fp_plugin

from vif_plug_ovs import constants
from vif_plug_vhostuser_fp.plug_ovs import linux_net
from vif_plug_vhostuser_fp import common


LOG = logging.getLogger(__name__)


class OvsFpPlugin(fp_plugin.FpPluginBase):
    """TBD

    FP plugin to deal with fastpath vhostuser ports for openvswitch
    """

    NIC_NAME_LEN = 14

    CONFIG_OPTS = (
        cfg.IntOpt('network_device_mtu',
                   default=1500,
                   help='MTU setting for network interface.',
                   deprecated_group="DEFAULT"),
        cfg.IntOpt('ovs_vsctl_timeout',
                   default=120,
                   help='Amount of time, in seconds, that ovs_vsctl should '
                   'wait for a response from the database. 0 is to wait '
                   'forever.',
                   deprecated_group="DEFAULT"),
    )

    def __init__(self, plugin_name):
        super(OvsFpPlugin, self).__init__(plugin_name, OvsFpPlugin.CONFIG_OPTS)

    def gen_port_name(self, prefix, id):
        return ("%s%s" % (prefix, id))[:OvsFpPlugin.NIC_NAME_LEN]

    def get_veth_pair_names(self, vif):
        return (self.gen_port_name("qvb", vif.id),
                self.gen_port_name("qvo", vif.id))

    def _create_vif_port(self, vif, vif_name, instance_info, **kwargs):
        linux_net.create_ovs_vif_port(
            vif.network.bridge,
            vif_name,
            vif.port_profile.interface_id,
            vif.address, instance_info.uuid,
            self.config.network_device_mtu,
            timeout=self.config.ovs_vsctl_timeout,
            **kwargs)

    def _plug_bridge(self, vif, instance_info):
        """Plug using hybrid strategy

        Create a per-VIF linux bridge, then link that bridge to the OVS
        integration bridge via a veth device, setting up the other end
        of the veth device just like a normal OVS port. Then boot the
        VIF on the linux bridge using standard libvirt mechanisms.
        """

        v1_name, v2_name = self.get_veth_pair_names(vif)

        common.ensure_bridge(vif.port_profile.bridge_name)

        common.add_bridge_port(vif.port_profile.bridge_name, vif.vif_name)

        if not linux_net.device_exists(v2_name):
            linux_net.create_veth_pair(v1_name, v2_name,
                                       self.config.network_device_mtu)
            common.add_bridge_port(vif.port_profile.bridge_name, v1_name)
            linux_net.ensure_ovs_bridge(vif.network.bridge,
                                        constants.OVS_DATAPATH_SYSTEM)
            self._create_vif_port(vif, v2_name, instance_info)

    def _unplug_bridge(self, vif, instance_info):
        """UnPlug using hybrid strategy

        Unhook port from OVS, unhook port from bridge, delete
        bridge, and delete both veth devices.
        """

        v1_name, v2_name = self.get_veth_pair_names(vif)

        common.delete_bridge(vif.port_profile.bridge_name, v1_name)

        linux_net.delete_ovs_vif_port(vif.network.bridge, v2_name,
                                      timeout=self.config.ovs_vsctl_timeout)

    def plug(self, vif, instance_info):
        """TBD

        Create and plug fastpath vhostuser port in bridge
        """

        mtu = self.config.network_device_mtu
        try:
            common.create_fp_dev(vif.vif_name, vif.path, vif.mode, mtu)
        except Exception:
            raise processutils.ProcessExecutionError()

        try:
            LOG.debug("OVS plug + fastpath")
            if vif.port_profile.hybrid_plug:
                self._plug_bridge(vif, instance_info)
            else:
                linux_net.ensure_ovs_bridge(vif.port_profile.bridge_name,
                                            constants.OVS_DATAPATH_SYSTEM)
                self._create_vif_port(vif, vif.vif_name, instance_info)
        except Exception:
            raise processutils.ProcessExecutionError()

    def unplug(self, vif, instance_info):
        """TBD

        Unplug and delete fastpath vhostuser port in bridge
        """

        try:
            if vif.port_profile.hybrid_plug:
                self._unplug_bridge(vif, instance_info)
            else:
                linux_net.delete_ovs_vif_port(
                    vif.network.bridge, vif.vif_name,
                    timeout=self.config.ovs_vsctl_timeout)
        except Exception:
            raise processutils.ProcessExecutionError()

        try:
            common.delete_fp_dev(vif.vif_name)
        except Exception:
            raise processutils.ProcessExecutionError()
