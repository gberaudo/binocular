#!/bin/sh

set -e

if [ ! $# -eq 3 ]
then
  echo "wrong number of arguments: $*"
  echo "Usage $0 <git_url> <branch> <sha>"
  exit 1
fi

set -x
git_url=$1
branch=$2
sha=$3

branch_directory="branches/$branch"
directory="branches/$branch/$sha"

mkdir -p $branch_directory
GIT_SSH=scripts/gitssh.sh git clone --depth 50 $git_url -b $branch $directory
cd $directory
git reset --hard $sha

# Build the project
cd -
config/handle_build_custom.sh $directory
