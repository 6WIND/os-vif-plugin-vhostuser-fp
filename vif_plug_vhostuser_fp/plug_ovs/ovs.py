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
from oslo_log import log as logging

from os_vif.internal.command import ip as ip_lib
from os_vif_plugin_vhostuser_fp import fp_plugin

from vif_plug_ovs import constants
from vif_plug_ovs import linux_net
from vif_plug_ovs import ovs
from vif_plug_ovs.ovsdb import ovsdb_lib

from vif_plug_vhostuser_fp import common


LOG = logging.getLogger(__name__)


class OvsFpPlugin(fp_plugin.FpPluginBase):
    """TBD

    FP plugin to deal with fastpath vhostuser ports for openvswitch
    """

    def __init__(self, plugin_name):
        super(OvsFpPlugin, self).__init__(plugin_name,
                                          ovs.OvsPlugin.CONFIG_OPTS)
        self.ovsdb = ovsdb_lib.BaseOVS(self.config)


    def _create_vif_port(self, vif, vif_name, instance_info, **kwargs):
        # NOTE(sean-k-mooney): As part of a partial fix to bug #1734320
        # we introduced the isolate_vif config option to enable isolation
        # of the vif prior to neutron wiring up the interface. To do
        # this we take advantage of the fact the ml2/ovs uses the
        # implementation defined VLAN 4095 as a dead VLAN to indicate
        # that all packets should be dropped. We only enable this
        # behaviour conditionally as it is not portable to SDN based
        # deployment such as ODL or OVN as such operator must opt-in
        # to this behaviour by setting the isolate_vif config option.
        if self.config.isolate_vif:
            kwargs['tag'] = constants.DEAD_VLAN
        self.ovsdb.create_ovs_vif_port(
            vif.network.bridge,
            vif_name,
            vif.port_profile.interface_id,
            vif.address, instance_info.uuid,
            self.get_mtu(vif),
            **kwargs)

    def _plug_bridge(self, vif, instance_info):
        """Plug using hybrid strategy

        Create a per-VIF linux bridge, then link that bridge to the OVS
        integration bridge via a veth device, setting up the other end
        of the veth device just like a normal OVS port. Then boot the
        VIF on the linux bridge using standard libvirt mechanisms.
        """

        v1_name, v2_name = ovs.OvsPlugin.get_veth_pair_names(vif)

        linux_net.ensure_bridge(vif.port_profile.bridge_name)

        linux_net.add_bridge_port(vif.port_profile.bridge_name, vif.vif_name)

        if not ip_lib.exists(v2_name):
            linux_net.create_veth_pair(v1_name, v2_name,
                                       self.get_mtu(vif))
            linux_net.add_bridge_port(vif.port_profile.bridge_name, v1_name)
            self.ovsdb.ensure_ovs_bridge(vif.network.bridge,
                                         constants.OVS_DATAPATH_SYSTEM)
            self._create_vif_port(vif, v2_name, instance_info)

    def _unplug_bridge(self, vif, instance_info):
        """UnPlug using hybrid strategy

        Unhook port from OVS, unhook port from bridge, delete
        bridge, and delete both veth devices.
        """
        v1_name, v2_name = ovs.OvsPlugin.get_veth_pair_names(vif)
        linux_net.delete_bridge(vif.port_profile.bridge_name, v1_name)
        # v2_name will be deleted in linux_net.delete_ovs_vif_port,
        # because by default the last parameter 'delete_netdev=True'
        # v1_name is its VETH pair, will be auto removed by kernel
        self.ovsdb.delete_ovs_vif_port(vif.network.bridge, v2_name)

    def plug(self, vif, instance_info):
        """TBD

        Create and plug fastpath vhostuser port in bridge
        """
        try:
            common.create_fp_dev(vif.vif_name, vif.path, vif.mode,
                                 self.get_mtu(vif))
        except Exception:
            raise processutils.ProcessExecutionError()

        try:
            LOG.info("Plugging fastpath vhostuser port in ovs")
            if vif.port_profile.hybrid_plug:
                self._plug_bridge(vif, instance_info)
            else:
                self.ovsdb.ensure_ovs_bridge(vif.network.bridge,
                                             constants.OVS_DATAPATH_SYSTEM)
                self._create_vif_port(vif, vif.vif_name, instance_info)
        except Exception:
            raise processutils.ProcessExecutionError()

    def unplug(self, vif, instance_info):
        """TBD

        Unplug and delete fastpath vhostuser port in bridge
        """

        try:
            LOG.info("Removing fastpath vhostuser port from ovs")
            if vif.port_profile.hybrid_plug:
                self._unplug_bridge(vif, instance_info)
            else:
                # pass 'delete_netdev=False', because vhostuser port
                # should be properly deleted later in common.delete_fp_dev
                self.ovsdb.delete_ovs_vif_port(vif.network.bridge,
                                               vif.vif_name,
                                               delete_netdev=False)
        except Exception:
            raise processutils.ProcessExecutionError()

        try:
            common.delete_fp_dev(vif.vif_name)
        except Exception:
            raise processutils.ProcessExecutionError()
