#!/bin/bash
myLocation=southeastasia
resourceGroup=ai102-cognitive-rg
#create resource group
if [ -z "$(az group list --query "[?name=='$resourceGroup'].name" --output tsv)" ]
then
    az group create --name $resourceGroup --location $myLocation
fi
#check if cognitive service exists
serviceType=SpeechServices
cognitiveServiceNameCurrent=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102-cognitive-$serviceType')].name" --output tsv)
#if service name exists, keep it
if [ -z "$cognitiveServiceNameCurrent" ]
then
    #create variable random name for cognitive service
    cognitiveServiceNamePrevious=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102-cognitive')].name" --output tsv)
    if [ ! -z "$cognitiveServiceNamePrevious" ]
    then
        #delete the current cognitive service
        az cognitiveservices account delete --name $cognitiveServiceNamePrevious --resource-group $resourceGroup
    fi
    cognitiveServiceNameCurrent=ai102-cognitive-$serviceType-$RANDOM
    #create cognitive service for text analytics
    az cognitiveservices account create --name $cognitiveServiceNameCurrent --kind $serviceType --sku F0 --resource-group $resourceGroup --location $myLocation --yes    
else
    echo "cognitive service name $cognitiveServiceNameCurrent exists"
fi
#get key for cognitive service
echo cognitiveServiceNameCurrent=$cognitiveServiceNameCurrent
#get the key for the cognitive service
key=$(az cognitiveservices account keys list --name $cognitiveServiceNameCurrent --resource-group $resourceGroup --query "key1" --output tsv)
export COG_SERVICE_REGION=$myLocation
export COG_SERVICE_KEY=$key
#export USE_MICROPHONE=True
echo COG_SERVICE_REGION=$COG_SERVICE_REGION, COG_SERVICE_KEY=$COG_SERVICE_KEY, USE_MICROPHONE=$USE_MICROPHONE, USE_VOICE=$USE_VOICE, USE_SSML=$USE_SSML
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
pushd $SCRIPTPATH
pip install --upgrade pip
pip install azure-cognitiveservices-speech==1.25.0
pip install playsound==1.2.2
pip install PyGObject==3.38.0
pip install pgi
python translator.py
popd
