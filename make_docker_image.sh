#!/bin/bash
## sole parameter is an integer indicating incremental daily version

if [[ ( $@ == "--help") ||  $@ == "-h" ]]; then
    echo "$0 <optional: --no-cache>"
    exit 1
fi

if [ $# -eq 1 ]; then
    NO_CACHE=$1
fi

#GIT_BRANCH=$1
#git checkout $GIT_BRANCH &&
#git pull &&
date_var=$(date +%Y.%m.%d.%H.%M%S)
BUILD_TAG=dbcawa/wlc_reporting:v$date_var
git log --pretty=medium -30 > ./git_history_recent &&
docker image build $NO_CACHE --tag $BUILD_TAG . &&
echo $BUILD_TAG &&
docker push $BUILD_TAG
