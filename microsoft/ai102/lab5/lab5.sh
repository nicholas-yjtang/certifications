#!/bin/bash
myLocation=southeastasia
resourceGroup=ai102-cognitive-rg
serviceType=TextAnalytics
#create resource group
#if group does not exist, create it
if [ -z "$(az group list --query "[?contains(name,'ai102-cognitive-rg')].name" --output tsv)" ]
then
    az group create --name $resourceGroup --location $myLocation
fi
#check if cognitive service exists
cognitiveServiceName=$(az cognitiveservices account list --resource-group ai102-cognitive-rg --query "[?contains(name,'ai102-cs-$serviceType')].name" --output tsv)
#if service name exists, keep it
if [ -z "$cognitiveServiceName" ]
then
    #delete the previous cognitive service
    cognitiveServiceNamePrevious=$(az cognitiveservices account list --resource-group ai102-cognitive-rg --query "[?contains(name,'ai102-cs')].name" --output tsv)
    if [ ! -z "$cognitiveServiceNamePrevious" ]
    then
        #delete the current cognitive service
        az cognitiveservices account delete --name $cognitiveServiceNamePrevious --resource-group $resourceGroup
    fi
    #create variable random name for cognitive service
    cognitiveServiceName=ai102-cs-$RANDOM
    #create cognitive service for text analytics
    az cognitiveservices account create --name $cognitiveServiceName --kind $serviceType --sku F0 --resource-group $resourceGroup --location $myLocation --yes    
else
    echo "cognitive service name exists"
fi
#get endpoint and key for cognitive service
echo cognitiveServiceName=$cognitiveServiceName
endpoint=$(az cognitiveservices account show --name $cognitiveServiceName --resource-group $resourceGroup --query "properties.endpoint" --output tsv)
key=$(az cognitiveservices account keys list --name $cognitiveServiceName --resource-group $resourceGroup --query "key1" --output tsv)
export COG_SERVICE_ENDPOINT=$endpoint
export COG_SERVICE_KEY=$key
#current script path
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
pushd $SCRIPTPATH
pip install azure-ai-textanalytics==5.1.0
python text-analysis.py
popd
