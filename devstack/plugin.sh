#!/bin/bash
#
# Copyright 2016 6WIND S.A.
#
# devstack/plugin.sh
# Functions to install the os-vif plugin for fast path vhostuser support

# Dependencies:
#
# ``functions`` file
# ``TOP_DIR`` must be defined

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace

# main loop
if is_service_enabled n-cpu; then
    if is_service_enabled os-vif-fp-plugin; then
        if [[ "$1" == "stack" && "$2" == "install" ]]; then
            setup_develop $DEST/os-vif-plugin-vhostuser-fp
        fi
    fi
fi

# Restore xtrace
$XTRACE
