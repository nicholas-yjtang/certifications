#!/bin/bash
myLocation=southeastasia
resourceGroup=ai102-cognitive-rg
#create resource group
#create resource group if it does not exist
if [ $(az group exists --name $resourceGroup) = false ]; then
    az group create --name $resourceGroup --location $myLocation
fi
#check if cognitive service exists
cognitiveServiceKind=TextAnalytics
cognitiveServiceName=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102-cs-$cognitiveServiceKind')].name" --output tsv)
#if service name exists, keep it
if [ -z "$cognitiveServiceName" ]
then
    #remove existing cognitive service because only 1 free tier allowed
    cognitiveServiceNamePrevious=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102')].name" --output tsv)
    if [ ! -z $cognitiveServiceNamePrevious ]; then
        echo deleting previous resource $cognitiveServiceNamePrevious
        az cognitiveservices account delete --name $cognitiveServiceNamePrevious --resource-group $resourceGroup
    fi    
    #create cognitive service for text analytics
    cognitiveServiceName=ai102-cs-$cognitiveServiceKind-$RANDOM    
    az cognitiveservices account create --name $cognitiveServiceName --kind $cognitiveServiceKind --sku F0 --resource-group $resourceGroup --location $myLocation --yes    
fi
#get endpoint and key for cognitive service
echo cognitiveServiceName=$cognitiveServiceName
subscriptionId=$(az account show --query id --output tsv)
#set alert on cognitive service, condition on list keys, signal type activity log, alert rule name is Key List Alert
#check if rule exists
ruleName="Key List Alert"
ruleExists=$(az monitor activity-log alert list --resource-group $resourceGroup --query "[?contains(name,'$ruleName')].name" --output tsv)
if [ -z "$ruleExists" ]
then
    az monitor activity-log alert create --resource-group $resourceGroup --name $ruleName --scope /subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.CognitiveServices/accounts/$cognitiveServiceName --condition category="Administrative" and operationName="Microsoft.CognitiveServices/accounts/listKeys/action" --description "Alert when cognitive service key is listed"
fi
keys=$(az cognitiveservices account keys list --name $cognitiveServiceName --resource-group $resourceGroup)
#display all fired alerts from the rule
az monitor activity-log alert show --resource-group $resourceGroup --name "$ruleName"