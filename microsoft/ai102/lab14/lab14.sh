#!/bin/bash
docker ps | grep botcomposer | awk '{print $1}' | if read -r containerid
then xargs docker stop $containerid
fi 
docker run -p 3000:3000 -p 3979-5000:3979-5000 -p 8000:8000 -v ./projects:/root/projects -d nicholasyjtang/botcomposer:latest