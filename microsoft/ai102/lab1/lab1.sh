#!/bin/bash
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate ai-102
pip install --upgrade pip
pip install python-dotenv
myLocation=southeastasia
resourceGroup=ai102-cognitive-rg
#create resource group if not exist
if [ $(az group exists --name $resourceGroup) = false ]; then
    az group create --name $resourceGroup --location $myLocation
fi
#if cognitive service does not exist, create it
cognitiveServiceKind=TextAnalytics
cognitiveServiceName=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102-cs-$cognitiveServiceKind')].name" --output tsv)
if [ -z $cognitiveServiceName ]; then
    #only allowed 1 single free tier cognitive service
    #deleting existing cognitive service
    cognitiveServiceNamePrevious=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102')].name" --output tsv)
    if [ ! -z $cognitiveServiceNamePrevious ]; then
        echo deleting previous resource $cognitiveServiceNamePrevious
        az cognitiveservices account delete --name $cognitiveServiceNamePrevious --resource-group $resourceGroup
    fi
    cognitiveServiceName=ai102-cs-$cognitiveServiceKind-$RANDOM    
    az cognitiveservices account create --name $cognitiveServiceName --kind $cognitiveServiceKind --sku F0 --resource-group $resourceGroup --location $myLocation --yes
fi

echo cognitiveServiceName=$cognitiveServiceName
#get endpoint and key for cognitive service
endpoint=$(az cognitiveservices account show --name $cognitiveServiceName --resource-group $resourceGroup --query "properties.endpoint" --output tsv)
key=$(az cognitiveservices account keys list --name $cognitiveServiceName --resource-group $resourceGroup --query "key1" --output tsv)
export COG_SERVICE_ENDPOINT=$endpoint
export COG_SERVICE_KEY=$key
echo COG_SERVICE_ENDPOINT=$endpoint and COG_SERVICE_KEY=$key

#get the current location of the bash script
scriptPath=$(dirname $(readlink -f $0))
pushd $scriptPath
python rest-client.py
popd