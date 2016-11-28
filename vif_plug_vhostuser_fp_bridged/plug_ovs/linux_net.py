# Derived from nova/network/linux_net.py
#
# Copyright 2016 6WIND S.A
# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""Implements vlans, bridges using linux utilities."""

import os

from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_utils import excutils

from vif_plug_ovs import constants
from vif_plug_ovs import exception
from vif_plug_ovs.i18n import _LE

from vif_plug_vhostuser_fp_bridged import privsep
from vif_plug_vhostuser_fp_bridged.common import set_device_mtu
from vif_plug_vhostuser_fp_bridged.common import device_exists

LOG = logging.getLogger(__name__)


def _ovs_vsctl(args, timeout=None):
    full_args = ['ovs-vsctl']
    if timeout is not None:
        full_args += ['--timeout=%s' % timeout]
    full_args += args
    try:
        return processutils.execute(*full_args)
    except Exception as e:
        LOG.error(_LE("Unable to execute %(cmd)s. Exception: %(exception)s"),
                  {'cmd': full_args, 'exception': e})
        raise exception.AgentError(method=full_args)


def _create_ovs_vif_cmd(bridge, dev, iface_id, mac,
                        instance_id, interface_type=None):
    cmd = ['--', '--if-exists', 'del-port', dev, '--',
            'add-port', bridge, dev,
            '--', 'set', 'Interface', dev,
            'external-ids:iface-id=%s' % iface_id,
            'external-ids:iface-status=active',
            'external-ids:attached-mac=%s' % mac,
            'external-ids:vm-uuid=%s' % instance_id]
    if interface_type:
        cmd += ['type=%s' % interface_type]
    return cmd


def _create_ovs_bridge_cmd(bridge, datapath_type):
    return ['--', '--may-exist', 'add-br', bridge,
            '--', 'set', 'Bridge', bridge, 'datapath_type=%s' % datapath_type]


@privsep.vif_plug.entrypoint
def create_ovs_vif_port(bridge, dev, iface_id, mac, instance_id,
                        mtu=None, interface_type=None, timeout=None):
    _ovs_vsctl(_create_ovs_vif_cmd(bridge, dev, iface_id,
                                   mac, instance_id,
                                   interface_type), timeout=timeout)
    # Note at present there is no support for setting the
    # mtu for vhost-user type ports.
    if mtu and interface_type != constants.OVS_VHOSTUSER_INTERFACE_TYPE:
        set_device_mtu(dev, mtu)
    else:
        LOG.debug("MTU not set on %(interface_name)s interface "
                  "of type %(interface_type)s.",
                  {'interface_name': dev,
                   'interface_type': interface_type})


@privsep.vif_plug.entrypoint
def delete_ovs_vif_port(bridge, dev, timeout=None):
    _ovs_vsctl(['--', '--if-exists', 'del-port', bridge, dev],
               timeout=timeout)


def _delete_net_dev(dev):
    """Delete a network device only if it exists."""
    if device_exists(dev):
        try:
            processutils.execute('ip', 'link', 'delete', dev,
                                 check_exit_code=[0, 2, 254])
            LOG.debug("Net device removed: '%s'", dev)
        except processutils.ProcessExecutionError:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed removing net device: '%s'"), dev)


@privsep.vif_plug.entrypoint
def create_veth_pair(dev1_name, dev2_name, mtu):
    """Create a pair of veth devices with the specified names,
    deleting any previous devices with those names.
    """
    for dev in [dev1_name, dev2_name]:
        _delete_net_dev(dev)

    processutils.execute('ip', 'link', 'add', dev1_name,
                         'type', 'veth', 'peer', 'name', dev2_name)
    for dev in [dev1_name, dev2_name]:
        processutils.execute('ip', 'link', 'set', dev, 'up')
        processutils.execute('ip', 'link', 'set', dev, 'promisc', 'on')
        set_device_mtu(dev, mtu)


@privsep.vif_plug.entrypoint
def ensure_ovs_bridge(bridge, datapath_type):
    _ovs_vsctl(_create_ovs_bridge_cmd(bridge, datapath_type))
