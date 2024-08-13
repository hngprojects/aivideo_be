#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <env>${NC}"
    exit 1
elif [[ "$1" != "dev" && "$1" != "staging" && "$1" != "prod" ]]; then
    echo -e "${RED}Invalid environment specified. Use dev, staging, or prod.${NC}"
    exit 1
fi

export ENV=$1
BRANCH=$1


if [ "$ENV" == "prod" ]; then
    BRANCH="main"
fi

echo -e "${BLUE}Preparing to deploy to the $ENV environment...${NC}"
echo -e "${YELLOW}Environment: $ENV${NC}"
echo -e "${YELLOW}Branch: $BRANCH${NC}"

echo -e "${GREEN}Loading Docker image from /tmp/nestjs_${ENV}.tar.gz...${NC}"
docker load --input aivideo-${ENV}.tar.gz

echo -e "${GREEN}Stashing local changes and Pulling the latest changes from branch $BRANCH...${NC}"
git add .
git stash
git checkout $BRANCH
git pull origin $BRANCH
docker stack deploy -c docker-compose.yaml -c compose/docker-compose.${ENV}.yaml  aivideo-be-${ENV}-stack 
rm -f aivideo-${ENV}.tar.gz


