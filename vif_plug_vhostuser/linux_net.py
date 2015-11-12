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

"""Implements vlans, bridges, and iptables rules using linux utilities."""

import os

from oslo_log import log as logging
from oslo_utils import excutils

from vif_plug_vhostuser.i18n import _LE
from vif_plug_vhostuser import processutils

LOG = logging.getLogger(__name__)


def _ovs_vsctl(args, timeout=timeout):
    full_args = ['ovs-vsctl', '--timeout=%s' % timeout] + args
    try:
        return processutils.execute(*full_args, run_as_root=True)
    except Exception as e:
        LOG.error(_LE("Unable to execute %(cmd)s. Exception: %(exception)s"),
                  {'cmd': full_args, 'exception': e})
        raise exception.AgentError(method=full_args)


def create_ovs_vif_port(bridge, dev, iface_id, mac, instance_id, mtu,
                        timeout=timeout):
    _ovs_vsctl(['--', '--if-exists', 'del-port', dev, '--',
                'add-port', bridge, dev,
                '--', 'set', 'Interface', dev,
                'external-ids:iface-id=%s' % iface_id,
                'external-ids:iface-status=active',
                'external-ids:attached-mac=%s' % mac,
                'external-ids:vm-uuid=%s' % instance_id],
                timeout=timeout)
    _set_device_mtu(dev, mtu)


def delete_ovs_vif_port(bridge, dev, timeout=timeout):
    _ovs_vsctl(['--', '--if-exists', 'del-port', bridge, dev],
               timeout=timeout)
    delete_net_dev(dev)


def ovs_set_vhostuser_port_type(dev, timeout=timeout):
    _ovs_vsctl(['--', 'set', 'Interface', dev, 'type=dpdkvhostuser'],
               timeout=timeout)


def device_exists(device):
    """Check if ethernet device exists."""
    return os.path.exists('/sys/class/net/%s' % device)


def delete_net_dev(dev):
    """Delete a network device only if it exists."""
    if device_exists(dev):
        try:
            processutils.execute('ip', 'link', 'delete', dev,
                                 check_exit_code=[0, 2, 254],
                                 run_as_root=True)
            LOG.debug("Net device removed: '%s'", dev)
        except processutils.ProcessExecutionError:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed removing net device: '%s'"), dev)


def _set_device_mtu(dev, mtu):
    """Set the device MTU."""
    processutils.execute('ip', 'link', 'set', dev, 'mtu', mtu,
                         check_exit_code=[0, 2, 254])
