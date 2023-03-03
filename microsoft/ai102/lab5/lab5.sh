#!/bin/bash
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate ai-102
pip install azure-ai-textanalytics==5.1.0
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
    #create variable random name for cognitive service
    congitiveServiceName=ai102-cognitive-$RANDOM
    #create cognitive service for text analytics
    az cognitiveservices account create --name $cognitiveServiceName --kind TextAnalytics --sku F0 --resource-group $resourceGroup --location $myLocation --yes    
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
python text-analysis.py
popd
