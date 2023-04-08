#!/bin/bash

# Sample script to build docker image, tag, and upload to ECR
# For debugging purposes only, official image should be built by CI/CD

if [[ $(uname -m) == 'arm64' ]]; then
  docker buildx build -f ./dockerfile.prod --platform linux/amd64 -t veeps_api .
else
  docker build -f ./dockerfile.prod -t veeps_api .
fi

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 695729695688.dkr.ecr.us-east-1.amazonaws.com

docker tag veeps_api:latest 695729695688.dkr.ecr.us-east-1.amazonaws.com/veeps_api:latest

docker push 695729695688.dkr.ecr.us-east-1.amazonaws.com/veeps_api:latest