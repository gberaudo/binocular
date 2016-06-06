#!/bin/bash

set -x
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
directory="$1"

cd $directory
git submodule update --recursive --init
cd -

CLONE="/home/nonroot/clone"
docker build -t binocular docker && docker run -v $DIR/$directory:$CLONE -w $CLONE --rm -t binocular ../build.sh
