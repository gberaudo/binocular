#!/bin/sh

set -e -x

mkdir /home/binocular
chmod 777 /build /home/binocular

groupadd -g ${GROUP_ID} binocular
useradd --shell /bin/bash --home /home/binocular --uid ${USER_ID} --gid ${GROUP_ID} binocular

su binocular -c "make dist"
su binocular -c "make check"
su binocular -c "make dist-examples"
su binocular -c "make dist-apidoc"
