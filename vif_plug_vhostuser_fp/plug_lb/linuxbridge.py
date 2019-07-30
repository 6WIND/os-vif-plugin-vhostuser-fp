#    Copyright 2016 6WIND S.A.
#
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

from os_vif_plugin_vhostuser_fp import fp_plugin

from vif_plug_linux_bridge import linux_bridge
from vif_plug_linux_bridge import linux_net
from vif_plug_vhostuser_fp import common


LOG = logging.getLogger(__name__)


class LinuxBridgeFpPlugin(fp_plugin.FpPluginBase):
    """TBD

    FP plugin to deal with fastpath vhostuser ports for linuxbridge
    """

    def __init__(self, plugin_name):
        super(LinuxBridgeFpPlugin, self).__init__(
            plugin_name,
            linux_bridge.LinuxBridgePlugin.CONFIG_OPTS)

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
            LOG.info("Plugging fastpath vhostuser port in bridge")
            linux_net.ensure_bridge(bridge=vif.port_profile.bridge_name,
                                    interface=vif.vif_name,
                                    mtu=self.get_mtu(vif))
        except Exception:
            raise processutils.ProcessExecutionError()

    def unplug(self, vif, instance_info):
        """TBD

        Unplug and delete fastpath vhostuser port in bridge
        """

        try:
            common.delete_fp_dev(vif.vif_name)
        except Exception:
            raise processutils.ProcessExecutionError()
