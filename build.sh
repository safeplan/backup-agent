#!/bin/bash
set -e

cd backup-agent-web
npm install
ng build --prod
cd ..
docker build -t safeplan/backup-agent .
docker push safeplan/backup-agent
