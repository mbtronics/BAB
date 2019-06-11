#!/usr/bin/env bash

docker build -t mbtronics/bab .
docker run -d -p 8084:80 --name bab mbtronics/bab
