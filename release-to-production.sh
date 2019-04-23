#!/bin/bash
set -e

./build.sh

docker build -t safeplan/backup-agent:1 .
docker push safeplan/backup-agent:1

echo "**************************************************"
echo "You released the :1 tagged version of the agent"
echo "which is used by production devices"
echo "**************************************************"
