# Deploy with a Azure DevOps CI/CD Pipeline

When setting up a deployment you will need to set the following variables for your pipeline manually:

|**Variable**|**Description**|
|-|-|
|AZURE_CLIENT_ID|The Client ID of the identity you want to use to deploy the application.|
|AZURE_ENV_NAME|The name of the Azure environment you want to deploy to, such as `copilot-usage-advanced-dashboard-dev`.|
|AZURE_LOCATION|The Azure location you want to deploy to, such as `eastus`, `westus`, etc.|
|AZURE_RESOURCE_GROUP|The name of the resource group you want to deploy to.|
|AZURE_SUBSCRIPTION_ID|The GUID for the subscription you want to deploy to.|
|AZURE_USER_PRINCIPAL_ID|The Object ID of a user you want to grant access to to the Azure Key Vault.|
|AZURE_TENANT_ID|The Azure Tenant ID of the identity you want to use to deploy the application.|
|GH_ORGANIZATION_SLUGS|This is your GitHub Organization name. This can be a comma-separated list of orgs if you want to index multiple orgs.|
|GH_PAT|This is your GitHub Personal Access Token.  Mark this variable as **secret** in your pipeline.|
|AZURE_AUTHENTICATION_ENABLED|Enable Entra ID Single-Sign On (SSO) authentication.|
|AZURE_AUTHENTICATION_CLIENT_ID|The Client ID of the Azure AD application.|
|AZURE_AUTHENTICATION_OPEN_ID_ISSUER|The OpenID Connect issuer URL for Azure AD.|

## Pipeline File Updates

If you are using Azure DevOps, make sure you change the value of the serviceConnectionName variable to be the name of your service connection in the `azure-dev.yml` file located in the `.azdo/pipelines` folder.

## Azure DevOps Updates

To create a service connection you can use the azd pipeline config --provider azdo command from the terminal.  You can read more here: [https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/pipeline-azure-pipelines](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/pipeline-azure-pipelines).

You will need to install the "Install azd" extension from the [marketplace](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.azd) in your Azure DevOps organization if you haven't already done so.

You will need to manually create the DevOps variables yourself in the Azure DevOps GUI.

---

## Script to Create Variable Group

To create this variable group, customize and run this command in Azure Cloud Shell.

After running this script, be sure to mark GH_PAT, AZURE_USER_PRINCIPAL_ID, AZURE_AUTHENTICATION_CLIENT_ID, and GRAFANA_PASSWORD as secrets.

You can also define these variables in the Azure DevOps portal per pipeline, but a variable group is more repeatable and scriptable.

```bash
az login

az pipelines variable-group create \
  --organization=https://dev.azure.com/<yourAzDOOrg>/ \
  --project='<yourAzDOProject>' \
  --name CopilotUsageDashboardSecrets \
  --variables \
      GH_PAT='<secretValue>' \
      AZURE_USER_PRINCIPAL_ID='<secretValue>' \
      AZURE_AUTHENTICATION_CLIENT_ID='<secretValue>' \
      GRAFANA_PASSWORD='<secretValue>' \
      AZURE_CLIENT_ID='<variableValue>' \
      AZURE_SUBSCRIPTION_ID='<variableValue>' \
      AZURE_TENANT_ID='<variableValue>' \
      AZURE_ENV_NAME='<variableValue>' \
      AZURE_LOCATION='<variableValue>' \
      AZURE_RESOURCE_GROUP='<variableValue>' \
      GH_ORGANIZATION_SLUGS='<variableValue>' \
      GRAFANA_USERNAME='<variableValue>' \
      AZURE_AUTHENTICATION_ENABLED='<variableValue>' \
      AZURE_AUTHENTICATION_OPEN_ID_ISSUER='<variableValue>'
```

---

[Home](../README.md#deployment)
