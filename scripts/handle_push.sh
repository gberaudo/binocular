#!/bin/sh

set -x
set -e

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
./handle_build_custom.sh $directory
