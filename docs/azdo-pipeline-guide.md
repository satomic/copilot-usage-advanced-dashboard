# Deploy with a Azure DevOps CI/CD Pipeline

When setting up a deployment you will need to set the following variables for your pipeline manually:

|**Type**|**Name**|**Required**|**Description**|
|-|-|-|-|
|Variable|AZURE_ENV_NAME|Yes|The name of the Azure environment you want to deploy to, such as `copilot-usage-advanced-dashboard-dev`|
|Variable|AZURE_LOCATION|Yes|The Azure location you want to deploy to, such as `eastus`, `westus`, etc.|
|Variable|AZURE_RESOURCE_GROUP|Yes|The name of the resource group you want to deploy to|
|Secret|GH_PAT|Yes|This is your GitHub Personal Access Token|
|Variable|GH_ORGANIZATION_SLUGS|Yes|This is your GitHub Organization name. This can be a comma-separated list of orgs if you want to index multiple orgs|
|Variable|GRAFANA_USERNAME|Yes/No|The username for Grafana|
|Secret|GRAFANA_PASSWORD|Yes/No|The password for Grafana|
|Variable|AZURE_CLIENT_ID|Yes|The Client ID of the identity you want to use to deploy the application|
|Variable|AZURE_SUBSCRIPTION_ID|Yes|The GUID for the subscription you want to deploy to|
|Variable|AZURE_TENANT_ID|Yes|The Azure Tenant ID of the identity you want to use to deploy the application|
|Variable|AZURE_USER_PRINCIPAL_ID|Yes|The Object ID of a user you want to grant access to to the Azure Key Vault|
|Variable|AZURE_AUTHENTICATION_ENABLED|Yes|Enable Entra ID Single-Sign On (SSO) authentication (true/false)|
|Variable|AZURE_AUTHENTICATION_CLIENT_ID|No|The Client ID of the Azure AD application|
|Variable|AZURE_AUTHENTICATION_OPEN_ID_ISSUER|No|The OpenID Connect issuer URL for Azure AD|

---

## Pipeline File Updates

If you are using Azure DevOps, make sure you change the value of the serviceConnectionName variable to be the name of your service connection in the `azure-dev.yml` file located in the `.azdo/pipelines` folder.

If you want this to update every time you push to the main branch, uncomment the trigger section in the [.azdo/pipelines/azure-dev.yml](../.azdo/pipelines/azure-dev.yml) file.

---

## Azure DevOps Updates

To create a service connection you can use the azd pipeline config --provider azdo command from the terminal.  You can read more here: [https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/pipeline-azure-pipelines](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/pipeline-azure-pipelines).

You will need to install the "Install azd" extension from the [marketplace](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.azd) in your Azure DevOps organization if you haven't already done so.

You will need to manually create the DevOps variables yourself in the Azure DevOps GUI or from the script below.

---

## Script to Create Variable Group

To create this variable group, customize and run this command in Azure Cloud Shell.

After running this script, be sure to mark GH_PAT, AZURE_USER_PRINCIPAL_ID, AZURE_AUTHENTICATION_CLIENT_ID, and GRAFANA_PASSWORD as secrets.

You can also define these variables in the Azure DevOps portal per pipeline, but a variable group is more repeatable and scriptable.

```bash
az login

az pipelines variable-group create `
  --organization=https://dev.azure.com/<yourAzDOOrg>/ `
  --project='<yourAzDOProject>' `
  --name CopilotUsageDashboardSecrets `
  --variables `
      AZURE_ENV_NAME='copilot-usage-advanced-dashboard-dev' `
      AZURE_RESOURCE_GROUP='rg-copilot-usage-advanced-dashboard-dev' `
      AZURE_LOCATION='eastus' `
      
      GH_PAT='<secretValue>' `
      GH_ORGANIZATION_SLUGS='<your-slug-or-slugs>' `
      GRAFANA_USERNAME='admin' `
      GRAFANA_PASSWORD='<secretValue>' `

      AZURE_CLIENT_ID='<variableValue>' `
      AZURE_SUBSCRIPTION_ID='<variableValue>' `
      AZURE_TENANT_ID='<variableValue>' `

      AZURE_USER_PRINCIPAL_ID='<optionalSecretValue>' `
      AZURE_AUTHENTICATION_CLIENT_ID='<optionalSecretValue>' `
      AZURE_AUTHENTICATION_ENABLED='<optionalVariableValue>' `
      AZURE_AUTHENTICATION_OPEN_ID_ISSUER='<optionalVariableValue>'
```

---

[Home](../README.md#deployment)
