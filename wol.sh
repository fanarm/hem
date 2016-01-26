#!/bin/bash
while [ -f /run/lock/nas.wol.lock ] ; do
    sudo wakeonlan 4C:E6:76:48:24:E5
    echo "WOL sent"
    sleep 60
done
