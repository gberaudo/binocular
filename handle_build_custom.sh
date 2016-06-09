#!/bin/bash

set -x
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
directory="$1"

cd $directory
git submodule update --recursive --init
cd -

docker build -t binocular docker && docker run -v $DIR/$directory:/build -e USER_ID=`id -u` -e GROUP_ID=`id -g` -w /build --rm -t binocular /root/build.sh
