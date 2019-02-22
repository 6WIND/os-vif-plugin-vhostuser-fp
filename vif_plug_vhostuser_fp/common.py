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

from fp_vdev_remote.utils import FP_VDEV_CMD
from fp_vdev_remote.utils import get_vdev_cmd

from vif_plug_vhostuser_fp import privsep

import os


def set_device_mtu(dev, mtu):
    """Set the device MTU."""
    processutils.execute('ip', 'link', 'set', dev, 'mtu', mtu,
                         check_exit_code=[0, 2, 254])


def device_exists(device):
    """Check if ethernet device exists."""
    return os.path.exists('/sys/class/net/%s' % device)


@privsep.vif_plug.entrypoint
def ensure_bridge(bridge):
    if not device_exists(bridge):
        processutils.execute('brctl', 'addbr', bridge)
        processutils.execute('brctl', 'setfd', bridge, 0)
        processutils.execute('brctl', 'stp', bridge, 'off')
        syspath = '/sys/class/net/%s/bridge/multicast_snooping'
        syspath = syspath % bridge
        processutils.execute('tee', syspath, process_input='0',
                             check_exit_code=[0, 1])
        disv6 = ('/proc/sys/net/ipv6/conf/%s/disable_ipv6' %
                 bridge)
        if os.path.exists(disv6):
            processutils.execute('tee',
                                 disv6,
                                 process_input='1',
                                 check_exit_code=[0, 1])


@privsep.vif_plug.entrypoint
def delete_bridge(bridge, dev):
    if device_exists(bridge):
        processutils.execute('brctl', 'delif', bridge, dev)
        processutils.execute('ip', 'link', 'set', bridge, 'down')
        processutils.execute('brctl', 'delbr', bridge)


@privsep.vif_plug.entrypoint
def add_bridge_port(bridge, dev):
    processutils.execute('ip', 'link', 'set', bridge, 'up')
    processutils.execute('brctl', 'addif', bridge, dev)


@privsep.vif_plug.entrypoint
def create_fp_dev(dev, sockpath, sockmode_qemu, mtu):
    fp_vdev_bin = FP_VDEV_CMD
    if fp_vdev_bin is None:
        fp_vdev_bin = get_vdev_cmd()
    if not device_exists(dev):
        sockmode = 'client' if sockmode_qemu == 'server' else 'server'
        processutils.execute(fp_vdev_bin, 'add', dev, '--sockpath', sockpath,
                             '--sockmode', sockmode, run_as_root=True)
        set_device_mtu(dev, mtu)
        processutils.execute('ip', 'link', 'set', dev, 'up',
                             check_exit_code=[0, 2, 254])


@privsep.vif_plug.entrypoint
def delete_fp_dev(dev):
    if device_exists(dev):
        fp_vdev_bin = FP_VDEV_CMD
        if fp_vdev_bin is None:
            fp_vdev_bin = get_vdev_cmd()
        processutils.execute(fp_vdev_bin, 'del', dev)
