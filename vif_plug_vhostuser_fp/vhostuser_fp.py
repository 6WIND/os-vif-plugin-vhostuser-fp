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

from os_vif import objects
from os_vif import plugin
from os_vif import exception

from os_vif_plugin_vhostuser_fp.i18n import _LE

from oslo_concurrency import processutils
from oslo_log import log as logging

from vif_plug_vhostuser_fp.plug_lb import linuxbridge
from vif_plug_vhostuser_fp.plug_ovs import ovs


PLUGIN_NAME = 'vhostuser_fp'
LOG = logging.getLogger(__name__)
OVS_FP = 'ovs_fp'
LB_FP = 'lb_fp'


class VhostuserFpPlugin(plugin.PluginBase):
    """TBD

    An os-vif plugin to bu used when pluggin/unpluggins fastpath vhostuser
    ports for bridged backends
    """

    def __init__(self, config):
        super(VhostuserFpPlugin, self).__init__(config)
        self.ovs = ovs.OvsFpPlugin(OVS_FP)
        self.lb = linuxbridge.LinuxBridgeFpPlugin(LB_FP)

    def describe(self):
        return objects.host_info.HostPluginInfo(
            plugin_name="vhostuser_fp",
            vif_info=[
                objects.host_info.HostVIFInfo(
                    vif_object_name=objects.vif.VIFVHostUser.__name__,
                    min_version="1.0",
                    max_version="1.0")
            ])

    def plug(self, vif, instance_info):
        if not isinstance(vif, objects.vif.VIFVHostUser):
            raise Exception

        try:
            LOG.debug("fastpath vhostuser plug for profile %s" % vif.port_profile)
            if isinstance(vif.port_profile,
                          objects.vif.VIFPortProfileFPOpenVSwitch):
                self.ovs.plug(vif, instance_info)
            elif isinstance(vif.port_profile,
                            objects.vif.VIFPortProfileFPBridge):
                self.lb.plug(vif, instance_info)
            elif isinstance(vif.port_profile,
                            objects.vif.VIFPortProfileFPTap):
                pass
            else:
                raise Exception
        except processutils.ProcessExecutionError:
            LOG.exception(_LE("Failed while plugging vif"))

    def unplug(self, vif, instance_info):
        if not isinstance(vif, objects.vif.VIFVHostUser):
            raise Exception

        try:
            if isinstance(vif.port_profile,
                          objects.vif.VIFPortProfileFPOpenVSwitch):
                self.ovs.unplug(vif, instance_info)
            elif isinstance(vif.port_profile,
                            objects.vif.VIFPortProfileFPBridge):
                self.lb.unplug(vif, instance_info)
            elif isinstance(vif.port_profile,
                            objects.vif.VIFPortProfileFPTap):
                pass
            else:
                raise Exception
        except processutils.ProcessExecutionError:
            LOG.exception(_LE("Failed while unplugging vif"))
