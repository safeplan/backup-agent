#!/bin/bash
set -e

docker build -t safeplan/backup-agent:1 .
docker push safeplan/backup-agent:1
