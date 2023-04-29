#!/bin/bash
myLocation=southeastasia
resourceGroup=ai102-cognitive-rg
#create resource group
if [ $(az group exists --name $resourceGroup) = false ]; then
    az group create --name $resourceGroup --location $myLocation
fi
#check if cognitive service exists
cognitiveServiceKind=TextAnalytics
cognitiveServiceName=$(az cognitiveservices account list --resource-group ai102-cognitive-rg --query "[?contains(name,'ai102-cs-$cognitiveServiceKind')].name" --output tsv)
#if service name exists, keep it
if [ -z "$cognitiveServiceName" ]
then
    #delete the previous cognitive service
    cognitiveServiceNamePrevious=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102')].name" --output tsv)
    if [ ! -z $cognitiveServiceNamePrevious ]; then
        echo deleting previous resource $cognitiveServiceNamePrevious
        az cognitiveservices account delete --name $cognitiveServiceNamePrevious --resource-group $resourceGroup
    fi  
    #create variable random name for cognitive service
    cognitiveServiceName=ai102-cs-$RANDOM
    #create cognitive service for text analytics
    az cognitiveservices account create --name $cognitiveServiceName --kind $cognitiveServiceKind --sku F0 --resource-group $resourceGroup --location $myLocation --yes    
else
    echo "cognitive service name exists"
fi
echo cognitiveServiceName=$cognitiveServiceName
#get endpoint and key for cognitive service
export endpoint=$(az cognitiveservices account show --name $cognitiveServiceName --resource-group $resourceGroup --query "properties.endpoint" --output tsv)
export key=$(az cognitiveservices account keys list --name $cognitiveServiceName --resource-group $resourceGroup --query "key1" --output tsv)
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
export output=$SCRIPTPATH/output
echo $endpoint,$key, $output, $input
#start docker container and have it run in the background
if [ ! -d "$output" ]; then
    mkdir $output
fi
#check if output folder is owned by user 999
if [ ! "$(stat -c %U $output)" = "999" ]; then
    sudo chown -R 999:999 $output
fi
#original example uses language detection, but the docker image has an issue, so changed to using sentiment instead as an example
docker compose up -d
curl -X POST "http://localhost:5000/text/analytics/v3.0/sentiment" -H "Content-Type: application/json" -d @$SCRIPTPATH/request.json