#!/bin/sh
read -p "What github repository do you want to access? (user/repository) " reply
cat > config.ini <<EOF
[main]
event_auth=`cat /proc/sys/kernel/random/uuid`
event_secret=`cat /proc/sys/kernel/random/uuid`
debug=True
allowed=$reply
EOF
