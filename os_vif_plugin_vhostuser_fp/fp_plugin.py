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

import abc
from oslo_config import cfg


CONF = cfg.CONF


class FpPluginBase(object):
    """Base class for all FP plugins."""

    # Override to provide a tuple of oslo_config.Opt instances for
    # the fp plugin specific config parameters
    CONFIG_OPTS = ()

    def __init__(self, plugin_name, config):
        """
        Initialize the plugin object with the provided config

        :param config: `oslo_config.ConfigOpts.GroupAttr` instance:
        """

        cfg_group_name = "os_vif_vhostuser_" + plugin_name
        cfg_group = cfg.OptGroup(cfg_group_name,
                                 "os-vif %s plugin options" % plugin_name)
        CONF.register_opts(config, group=cfg_group)
        self.config = getattr(CONF, cfg_group_name)

    @abc.abstractmethod
    def plug(self, vif, instance_info):
        """
        Given a fp_plug_type, perform operations to plug the VIF properly.

        :param vif: `os_vif.objects.VIF` object.
        :param instance_info: `os_vif.objects.InstanceInfo` object.
        :raises `processutils.ProcessExecutionError`. Plugins implementing
                this method should let `processutils.ProcessExecutionError`
                bubble up.
        """

        pass

    @abc.abstractmethod
    def unplug(self, vif, instance_info):
        """
        Given a fp_plug_type, perform operations to unplug the VIF properly.

        :param vif: `os_vif.objects.VIF` object.
        :param instance_info: `os_vif.objects.InstanceInfo` object.
        :raises `processutils.ProcessExecutionError`. Plugins implementing
                this method should let `processutils.ProcessExecutionError`
                bubble up.
        """

        pass
