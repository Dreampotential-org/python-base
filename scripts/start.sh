#!/bin/bash

set -x

docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.yml build
#export db_host=`curl http://169.254.169.254/latest/meta-data/public-ipv4`
docker-compose -f docker-compose.yml up -d
# docker-compose -f docker-compose.yml logs -f

