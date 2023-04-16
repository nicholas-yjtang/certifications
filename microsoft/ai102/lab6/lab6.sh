#!/bin/bash
myLocation=southeastasia
resourceGroup=ai102-cognitive-rg
#create resource group
#if resource group does not exist, create it
if [ -z "$(az group list --query "[?name=='$resourceGroup'].name" --output tsv)" ]
then
    az group create --name $resourceGroup --location $myLocation
fi
#check if cognitive service exists
cognitiveServiceKind=TextTranslation
cognitiveServiceTranslationName=$(az cognitiveservices account list --resource-group ai102-cognitive-rg --query "[?contains(name,'ai102-cs-$cognitiveServiceKind')].name" --output tsv)
#if service name exists, keep it
if [ -z "$cognitiveServiceTranslationName" ]
then
    #create variable random name for cognitive service
    cognitiveServiceName=$(az cognitiveservices account list --resource-group ai102-cognitive-rg --query "[?contains(name,'ai102')].name" --output tsv)
    if [ ! -z "$cognitiveServiceName" ]
    then
        #delete the current cognitive service
        az cognitiveservices account delete --name $cognitiveServiceName --resource-group $resourceGroup
    fi
    cognitiveServiceTranslationName=ai102-cs-$cognitiveServiceKind-$RANDOM
    #create cognitive service for text analytics
    az cognitiveservices account create --name $cognitiveServiceTranslationName --kind TextTranslation --sku F0 --resource-group $resourceGroup --location $myLocation --yes    
else
    echo "cognitive service name exists"
fi
#get key for cognitive service
echo cognitiveServiceTranslationName=$cognitiveServiceTranslationName
#get the key for the cognitive service
key=$(az cognitiveservices account keys list --name $cognitiveServiceTranslationName --resource-group $resourceGroup --query "key1" --output tsv)
export COG_SERVICE_REGION=$myLocation
export COG_SERVICE_KEY=$key
echo COG_SERVICE_REGION=$COG_SERVICE_REGION, COG_SERVICE_KEY=$COG_SERVICE_KEY
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
pushd $SCRIPTPATH
pip install azure-ai-textanalytics==5.1.0
python text-translation.py
popd
