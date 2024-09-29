#!/bin/bash
sudo journalctl --vacuum-size=100M
sudo find /var/log -type f -iname *.gz -delete 
sudo apt-get clean


set -eu
snap list --all | awk '/disabled/{print $1, $3}' |
    while read snapname revision; do
        sudo snap remove "${snapname}" --revision="${revision}"
    done

sudo truncate -s 0 /var/log/syslog