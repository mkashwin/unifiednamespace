#!/bin/bash
# spell-checker:disable
sudo journalctl --vacuum-size=100M
# trunk-ignore(shellcheck/SC2035)
sudo find /var/log -type f -iname *.gz -delete 
sudo apt-get clean


set -eu
# trunk-ignore(shellcheck/SC2312)
snap list --all | awk '/disabled/{print $1, $3}' |
    while read -r snapname revision; do
        sudo snap remove "${snapname}" --revision="${revision}"
    done

sudo truncate -s 0 /var/log/syslog
# spell-checker:enable