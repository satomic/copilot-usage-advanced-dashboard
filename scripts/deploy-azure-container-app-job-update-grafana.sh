#!/bin/bash

# Check if 'azd' command is available
if ! command -v azd &> /dev/null; then
    echo "Error: 'azd' command is not found. Please ensure you have 'azd' installed."
    echo "For installation instructions, visit: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd"
    exit 1
fi

# Check if 'az' command is available
if ! command -v az &> /dev/null; then
    echo "Error: 'az' command is not found. Please ensure you have 'az' installed."
    echo "For installation instructions, visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

echo ""
echo "Loading azd .env file from current environment"
echo ""

while IFS='=' read -r key value; do
    if [[ $key && $value ]]; then
        export "$key"="${value%\"}"
    fi
done < <(azd env get-values)

if [ $? -ne 0 ]; then
    echo "Failed to load environment variables from azd environment"
    exit 1
else
    echo "Successfully loaded env vars from .env file."
fi

if [ "${AZD_IS_PROVISIONED,,}" != "true" ]; then
    echo "Azure resources are not provisioned. Please run 'azd provision' to set up the necessary resources before running this script."
    exit 1
fi

resourceGroup="$AZURE_RESOURCE_GROUP_NAME"
environment="$AZURE_CONTAINER_APPS_ENVIRONMENT_NAME"
jobName="$AZURE_RESOURCE_UPDATE_GRAFANA_NAME"
loginServer="$AZURE_CONTAINER_REGISTRY_ENDPOINT"
tag="azd-$(date +'%Y%m%d%H%M%S')"
image="$AZURE_CONTAINER_REGISTRY_ENDPOINT/copilot-usage-advanced-dashboard/update-grafana-job:$tag"
projectDir="$(realpath "$(dirname "$0")/../src/cpuad-updater/grafana")"

echo "Resource Group: $resourceGroup"
echo "Environment: $environment"
echo "Job Name: $jobName"
echo "Login Server: $loginServer"
echo "Image: $image"
echo "Project Directory: $projectDir"

echo "Building and pushing Docker image using Azure Container Registry tasks..."
az acr build --registry "$loginServer" --image "$image" --file "$projectDir/Dockerfile" "$projectDir"
if [ $? -ne 0 ]; then
    echo "ACR build failed"
    exit 1
fi
echo "ACR build and push succeeded"

echo "Updating Azure Container App Job..."
az containerapp job update --name "$jobName" --resource-group "$resourceGroup" --image "$image"
if [ $? -ne 0 ]; then
    echo "Container App Job update failed"
    exit 1
fi
echo "Container App Job update succeeded"

echo "Deployed Azure Container App Job successfully"

echo "Starting Azure Container App Job..."
az containerapp job start --name "$jobName" --resource-group "$resourceGroup"
if [ $? -ne 0 ]; then
    echo "Container App Job start failed"
    exit 1
fi

echo "Container App Job started successfully"

portalUrl="https://portal.azure.com/#@$AZURE_TENANT_ID/resource$AZURE_CONTAINER_APP_JOB_URL"

echo -n "You can view the Container App Job in the Azure Portal: "
echo -e "\033[34m$portalUrl\033[0m"