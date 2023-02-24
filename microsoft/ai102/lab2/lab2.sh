#!/bin/bash
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate ai-102
pip install --upgrade pip
pip install python-dotenv
pip install azure-ai-textanalytics
pip install azure-core
pip install azure-keyvault-secrets
pip install azure-identity 
myLocation=southeastasia
resourceGroup=ai102-cognitive-rg
#create resource group if it does not exist
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
endpoint=$(az cognitiveservices account show --name $cognitiveServiceName --resource-group $resourceGroup --query "properties.endpoint" --output tsv)
key=$(az cognitiveservices account keys list --name $cognitiveServiceName --resource-group $resourceGroup --query "key1" --output tsv)
echo using $endpoint and $key
curl -s -X POST "$endpoint/text/analytics/v3.1/languages?" -H "Content-Type: application/json" -H "Ocp-Apim-Subscription-Key: $key" --data-ascii "{'documents':[{'id':1,'text':'hello'}]}"
echo 
echo "regenerating key"
az cognitiveservices account keys regenerate --name $cognitiveServiceName --resource-group $resourceGroup --key-name key1
echo trying to perform operation with old key $key                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
curl -s -X POST "$endpoint/text/analytics/v3.1/languages?" -H "Content-Type: application/json" -H "Ocp-Apim-Subscription-Key: $key" --data-ascii "{'documents':[{'id':1,'text':'hello'}]}"
echo 
#update the key
key=$(az cognitiveservices account keys list --name $cognitiveServiceName --resource-group $resourceGroup --query "key1" --output tsv)
echo "updated the key with $key"
curl -s -X POST "$endpoint/text/analytics/v3.1/languages?" -H "Content-Type: application/json" -H "Ocp-Apim-Subscription-Key: $key" --data-ascii "{'documents':[{'id':1,'text':'hello'}]}"
echo
#create keyvault
#check if keyvault exists
az keyvault list --resource-group $resourceGroup --query  "[?contains(name,'ai102-keyvault')].name"  --output tsv | while read keyVaultName
do
    echo deleting $keyVaultName
    az keyvault delete --name $keyVaultName --resource-group $resourceGroup
done

echo creatin a new keyvault
keyVaultName=ai102-keyvault-$RANDOM
echo keyVaultName=$keyVaultName
az keyvault create --name $keyVaultName --resource-group $resourceGroup --location $myLocation
#add key to keyvault, the key is hardcoded to match the code in the python file
az keyvault secret set --name Cognitive-Services-Key --value $key --vault-name $keyVaultName 

#check if service principal exists
az ad sp list --query "[?contains(displayName,'ai102')].id" --output tsv | while read servicePrincipalId
do
    echo deleting $servicePrincipalId
    az ad sp delete --id $servicePrincipalId
done

subscriptionId=$(az account show --query "id" --output tsv)
servicePrincipalName=ai102-service-principal-$RANDOM
echo servicePrincipalName=$servicePrincipalName
sp_object=$(az ad sp create-for-rbac --name $servicePrincipalName --role contributor --scopes /subscriptions/$subscriptionId/resourceGroups/$resourceGroup)
appId=$(echo $sp_object | jq -r '.appId')
appPassword=$(echo $sp_object | jq -r '.password')
#add access policy to keyvault
echo appId=$appId, appPassword=$appPassword
az keyvault set-policy --name $keyVaultName --spn $appId --secret-permissions get list

export COG_SERVICE_ENDPOINT=$endpoint
export KEY_VAULT=$keyVaultName
export TENANT_ID=$(az account show --query "tenantId" --output tsv)
export APP_PASSWORD=$appPassword
export APP_ID=$appId
echo COG_SERVICE_ENDPOINT=$COG_SERVICE_ENDPOINT, KEY_VAULT=$KEY_VAULT, TENANT_ID=$TENANT_ID, APP_ID=$APP_ID, APP_PASSWORD=$APP_PASSWORD

scriptPath=$(dirname $(readlink -f $0))
pushd $scriptPath
python keyvault-client.py
popd