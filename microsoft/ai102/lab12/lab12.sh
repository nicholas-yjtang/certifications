#!/bin/bash
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate ai-102
myLocation=westeurope
resourceGroup=ai102-cognitive-rg-westeurope
#check if resource group exists, it not create it
if [ -z "$(az group exists --name $resourceGroup)" ]
then
    az group create --name $resourceGroup --location $myLocation
fi
#check if cognitive service exists
serviceType=TextAnalytics
serviceTypeName=${serviceType//./_}
cognitiveServiceNameCurrent=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102-cs-$serviceTypeName')].name" --output tsv)
#if service name exists, keep it
if [ -z "$cognitiveServiceNameCurrent" ]
then
    #create variable random name for cognitive service
    echo creating new cognitive service
    cognitiveServiceNamePrevious=$(az cognitiveservices account list --resource-group $resourceGroup --query "[?contains(name,'ai102')].name" --output tsv)
    if [ ! -z "$cognitiveServiceNamePrevious" ]
    then
        #delete the current cognitive service
        echo deleting previous resource $cognitiveServiceNamePrevious
        az cognitiveservices account delete --name $cognitiveServiceNamePrevious --resource-group $resourceGroup
    fi
    cognitiveServiceNameCurrent=ai102-cs-$serviceTypeName-$RANDOM
    #create cognitive service for text analytics
    echo creating new resource $cognitiveServiceNameCurrent
    az cognitiveservices account create --name $cognitiveServiceNameCurrent --kind $serviceType --sku F0 --resource-group $resourceGroup --location $myLocation --yes    
else
    echo "cognitive service name $cognitiveServiceNameCurrent exists"
fi
#get key for cognitive service
echo cognitiveServiceNameCurrent=$cognitiveServiceNameCurrent
#get the endpoint for the cognitive service
endpoint=$(az cognitiveservices account show --name $cognitiveServiceNameCurrent --resource-group $resourceGroup --query "properties.endpoint" --output tsv)
#get the key for the cognitive service
key=$(az cognitiveservices account keys list --name $cognitiveServiceNameCurrent --resource-group $resourceGroup --query "key1" --output tsv)

searhServiceName=$(az search service list --resource-group $resourceGroup --query "[?contains(name,'ai102-search')].name" --output tsv)
#if service name exists, keep it
if [ -z "$searhServiceName" ]
then
    #create variable random name for cognitive service
    echo creating new search service
    searhServiceName=ai102-search-$RANDOM
    az search service create --name $searhServiceName --resource-group ai102-cognitive-rg-westeurope --sku free --location $myLocation
fi
echo searhServiceName=$searhServiceName
#get azure search key
subscriptionId=$(az account show --query "id" --output tsv)
searchKey=$(az search admin-key show --resource-group $resourceGroup --service-name $searhServiceName --query "primaryKey" --output tsv)
#if search service is not linked to cognitive service, link it
if [ -z "$(az cognitiveservices account show --name $cognitiveServiceNameCurrent --resource-group $resourceGroup --query "properties.apiProperties.qnaAzureSearchEndpointId" --output tsv)" ]
then
    echo linking search service to cognitive service
    az cognitiveservices account update --name $cognitiveServiceNameCurrent --resource-group $resourceGroup --api-properties qnaAzureSearchEndpointId=/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Search/searchServices/$searhServiceName qnaAzureSearchEndpointKey=$searchKey
fi
#deploy the custom question answer project to language studio
PROJECTNAME=LearnFAQ2
APIVERSION=2022-10-01-preview
#get script current path
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
#delete the project if it exists
echo "deleting project $PROJECTNAME"
operationlocation=$(curl -D - -s -X DELETE "$endpoint/language/query-knowledgebases/projects/$PROJECTNAME?api-version=$APIVERSION" -H "Ocp-Apim-Subscription-Key: $key" | grep -i operation-location | cut -d' ' -f2 | tr -d '\r')
if [ ! -z "$operationlocation" ]; then
    deleteStatus=$(curl -s $operationlocation -H "Ocp-Apim-Subscription-Key: $key" | jq -r '.status')
    echo "deleteStatus=$deleteStatus"
    while [ "$deleteStatus" == "running" ] || [ "$deleteStatus" == "notStarted" ]; do
        echo "deleting in progress"
        sleep 5
        deleteStatus=$(curl -s $operationlocation -H "Ocp-Apim-Subscription-Key: $key" | jq -r '.status')
    done
fi
response=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$endpoint/language/query-knowledgebases/projects/$PROJECTNAME?api-version=$APIVERSION" -H "Content-Type: application/json"  -H "Ocp-Apim-Subscription-Key: $key" -d @$SCRIPTPATH/settings.json)
#check response from curl is status code 200
echo response=$response
#curl -s -v $endpoint/language/query-knowledgebases/projects/LearnFAQ/sources?api-version=$APIVERSION -H "Ocp-Apim-Subscription-Key: $key"
#curl -s -v $endpoint/language/query-knowledgebases/projects/LearnFAQ/qnas?api-version=$APIVERSION -H "Ocp-Apim-Subscription-Key: $key"
if [ "$response" -eq 200 ] || [ "$response" -eq 201 ];
then

    #add the source for Learn FAQ
    echo "adding source for Learn FAQ"
    #curl -v -s -X PATCH "$endpoint/language/query-knowledgebases/projects/$PROJECTNAME/sources?api-version=$APIVERSION" -H "Content-Type: application/json"  -H "Ocp-Apim-Subscription-Key: $key" -d @$SCRIPTPATH/source.json
    operationlocation=$(curl -D - -s -X PATCH "$endpoint/language/query-knowledgebases/projects/$PROJECTNAME/sources?api-version=$APIVERSION" -H "Content-Type: application/json"  -H "Ocp-Apim-Subscription-Key: $key" -d @$SCRIPTPATH/source.json | grep -i operation-location | cut -d' ' -f2 | tr -d '\r')    operationlocation=$(echo $operationlocation | tr -d '\r')
    echo "operationlocation=$operationlocation"
    #check if operation is completed
    if [ ! -z "$operationlocation" ]; then
        sourceStatus=$(curl -s $operationlocation -H "Ocp-Apim-Subscription-Key: $key" | jq -r '.status')
        echo "sourceStatus=$sourceStatus"
        while [ "$sourceStatus" == "running" ] || [ "$sourceStatus" == "notStarted" ]; do
            echo "source in progress"
            sleep 5
            sourceStatus=$(curl -s $operationlocation -H "Ocp-Apim-Subscription-Key: $key" | jq -r '.status')
        done
        if [ "$sourceStatus" == "succeeded" ]; then
            echo "source updated, going to update qna"
            #manually update qna
            cp $SCRIPTPATH/qna.template.json $SCRIPTPATH/qna.json
            current_index=$(curl -s $endpoint/language/query-knowledgebases/projects/LearnFAQ2/qnas?api-version=$APIVERSION -H "Ocp-Apim-Subscription-Key: $key" | jq '.[] | length')
            id1=$(($current_index+1))
            id2=$(($current_index+2))
            sed -i "s/\"{ID1}\"/$id1/g" $SCRIPTPATH/qna.json
            sed -i "s/\"{ID2}\"/$id2/g" $SCRIPTPATH/qna.json
            #curl -v -s -X PATCH "$endpoint/language/query-knowledgebases/projects/$PROJECTNAME/qnas?api-version=$APIVERSION" -H "Content-Type: application/json"  -H "Ocp-Apim-Subscription-Key: $key" -d @$SCRIPTPATH/qna.json
            operationlocation=$(curl -D - -s -X PATCH "$endpoint/language/query-knowledgebases/projects/$PROJECTNAME/qnas?api-version=$APIVERSION" -H "Content-Type: application/json"  -H "Ocp-Apim-Subscription-Key: $key" -d @$SCRIPTPATH/qna.json | grep -i operation-location | cut -d' ' -f2 | tr -d '\r')
            echo "operationlocation=$operationlocation"
            #check if operation is completed
            if [ ! -z "$operationlocation" ]; then
                qnaStatus=$(curl -s $operationlocation -H "Ocp-Apim-Subscription-Key: $key" | jq -r '.status')
                echo "qnaStatus=$qnaStatus"
                while [ "$qnaStatus" == "running" ] || [ "$qnaStatus" == "notStarted" ]; do
                    echo "qna in progress"
                    sleep 5
                    qnaStatus=$(curl -s $operationlocation -H "Ocp-Apim-Subscription-Key: $key" | jq -r '.status')
                done
                if [ "$qnaStatus" == "succeeded" ]; then
                    echo "qna updated, deploying the project"
                    #deploy the project
                    deploymentName=production
                    #curl -v -s -X PUT "$endpoint/language/authoring/query-knowledgebases/projects/$PROJECTNAME/deployments/$deploymentName?api-version=$APIVERSION" -H "Ocp-Apim-Subscription-Key: $key " -H "Content-Length: 0"
                    operationlocation=$(curl -D - -s -X PUT "$endpoint/language/authoring/query-knowledgebases/projects/$PROJECTNAME/deployments/$deploymentName?api-version=$APIVERSION" -H "Content-Length: 0" -H "Ocp-Apim-Subscription-Key: $key" | grep -i operation-location | cut -d' ' -f2 | tr -d '\r')
                    echo "operationlocation=$operationlocation"
                    #check if operation is completed
                    if [ ! -z "$operationlocation" ]; then
                        deployStatus=$(curl -s $operationlocation -H "Ocp-Apim-Subscription-Key: $key" | jq -r '.status')
                        echo "deployStatus=$deployStatus"
                        while [ "$deployStatus" == "running" ] || [ "$deployStatus" == "notStarted" ]; do
                            echo "deploy in progress"
                            sleep 5
                            deployStatus=$(curl -s $operationlocation -H "Ocp-Apim-Subscription-Key: $key" | jq -r '.status')
                        done
                        if [ "$deployStatus" == "succeeded" ]; then
                            echo "deploy succeeded"
                            predictionEndpoint="$endpoint/language/:query-knowledgebases?projectName=$PROJECTNAME&deploymentName=$deploymentName&api-version=$APIVERSION"
                            echo "predictionEndpoint=$predictionEndpoint"
                            #calling prediction endpoint
                            curl -X POST $predictionEndpoint -H "Ocp-Apim-Subscription-Key: $key" -H "Content-Type: application/json" -d "{'question': 'What is a learning Path?' }"
                            #create the web bot

                        else
                            echo "deploy failed, $deployStatus"
                        fi
                    fi
                else
                    echo "qna failed"
                fi
            fi

        else
            echo "source failed"
        fi
    fi    
fi
#deploy the qna maker service
#echo deploying qna maker service
#az group deployment create --resource-group $resourceGroup --template-file ./qna-maker.json --parameters cognitiveServiceName=$cognitiveServiceNameCurrent searchServiceName=$searhServiceName searchServiceKey=$searchKey

#set prediction_url="YOUR_PREDICTION_ENDPOINT"
#set key="YOUR_KEY"
#curl -X POST !prediction_url! -H "Ocp-Apim-Subscription-Key: !key!" -H "Content-Type: application/json" -d "{'question': 'What is a learning Path?' }"
#curl -s -v $endpoint/language/query-knowledgebases/projects/$PROJECTNAME/sources?api-version=$APIVERSION -H "Ocp-Apim-Subscription-Key: $key"
#curl -s -v $endpoint/language/query-knowledgebases/projects/LearnFAQ/qnas?api-version=$APIVERSION -H "Ocp-Apim-Subscription-Key: $key"

