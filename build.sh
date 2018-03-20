#!/bin/bash
set -e

#cd backup-agent-web
#npm install
#ng build --prod
#cd ..
docker build -t safeplan/backup-agent:1 .
docker push safeplan/backup-agent:1
