#!/bin/bash

docker stop public-procurementer
docker rm public-procurementer
docker build -t public-procurementer .
docker run -d \
    --network im_network \
    -p 5001:5001 \
    --env-file env.list \
    -v ./uploads:/usr/local/public-procurementer/uploads \
    --name public-procurementer --restart unless-stopped public-procurementer
