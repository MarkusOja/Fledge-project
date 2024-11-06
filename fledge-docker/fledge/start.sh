#!/bin/bash

# from https://github.com/fledge-power/fledgepower-deployment/blob/main/s61850-n104-ubuntu2004/fledge/start.sh

# Unprivileged Docker containers do not have access to the kernel log. This prevents an error when starting rsyslogd.
sed -i '/imklog/s/^/#/' /etc/rsyslog.conf

service rsyslog start
/usr/local/fledge/bin/fledge start
