#!/bin/sh

set -e -x

chmod 777 /build
groupadd -g ${GROUP_ID} binocular
useradd --shell /bin/bash --uid ${USER_ID} --gid ${GROUP_ID} binocular

su binocular -c "make dist"
su binocular -c "make check"
su binocular -c "make dist-examples"
su binocular -c "make dist-apidoc"
