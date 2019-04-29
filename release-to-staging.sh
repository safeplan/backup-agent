#!/bin/bash
set -e

./build.sh

docker build -t safeplan/backup-agent:STAGING .
docker push safeplan/backup-agent:STAGING


echo "*****************************************************************"
echo "You released the :STAGING tagged version of the agent"
echo "which is only used by specific test devices (currently just Roger's Synology)"
echo "To release to production devices, call ./release-to-production.sh"
echo "*****************************************************************"
