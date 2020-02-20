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

from os_vif.internal.ip.api import ip as ip_lib
from oslo_concurrency import processutils

from fp_vdev_remote.vdev_utils import get_vdev_cmd

from vif_plug_ovs import linux_net
from vif_plug_vhostuser_fp import privsep


FP_VDEV_CMD = None


@privsep.vif_plug.entrypoint
def create_fp_dev(dev, sockpath, sockmode_qemu, mtu):
    global FP_VDEV_CMD
    if FP_VDEV_CMD is None:
        FP_VDEV_CMD = get_vdev_cmd()
    if not ip_lib.exists(dev):
        sockmode = 'client' if sockmode_qemu == 'server' else 'server'
        processutils.execute(FP_VDEV_CMD, 'add', dev, '--sockpath', sockpath,
                             '--sockmode', sockmode, run_as_root=True)
        linux_net.set_device_mtu(dev, mtu)
        processutils.execute('ip', 'link', 'set', dev, 'up',
                             check_exit_code=[0, 2, 254])


@privsep.vif_plug.entrypoint
def delete_fp_dev(dev):
    global FP_VDEV_CMD
    if ip_lib.exists(dev):
        if FP_VDEV_CMD is None:
            FP_VDEV_CMD = get_vdev_cmd()
        processutils.execute(FP_VDEV_CMD, 'del', dev)
