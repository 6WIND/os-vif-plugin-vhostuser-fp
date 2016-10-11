# Derived from nova/network/linux_net.py
#
# Copyright 2016 6WIND S.A.
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

"""Implements linuxbridge specific linux utilities."""

from oslo_concurrency import processutils

from vif_plug_vhostuser_fp_bridged import privsep

@privsep.vif_plug.entrypoint
def delete_bridge_port(bridge, dev):
    processutils.execute('ip', 'link', 'set', bridge, 'down')
    processutils.execute('brctl', 'delif', bridge, dev)
