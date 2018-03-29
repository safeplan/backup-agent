#!/bin/bash
set -e

#cd backup-agent-web
#npm install
#ng build --prod
#cd ..

cp fm/index.html api/browse

rm -rf api/browse/dist
cp -r fm/dist api/browse/dist

rm -rf api/browse/node_modules
cp -r fm/node_modules api/browse/node_modules

docker build -t safeplan/backup-agent:1 .
docker push safeplan/backup-agent:1
