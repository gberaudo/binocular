#!/bin/bash

set -e
if [ ! $# -eq 1 ]
then
  echo "wrong number of arguments: $*"
  echo "Usage $0 <relative directory to cloned code>"
  exit 1
fi


set -x
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
directory="$1"

cd $directory
git submodule update --recursive --init
cd -

docker build -t binocular config/docker && docker run -v $DIR/$directory:/build -e USER_ID=`id -u` -e GROUP_ID=`id -g` -w /build --rm -t binocular /build.sh
