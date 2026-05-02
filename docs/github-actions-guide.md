# Deploy with a GitHub Action

When setting up a deployment you will need to set the following variables and secrets in your GitHub environment manually:

|**Type**|**Name**|**Required**|**Description**|
|-|-|-|-|
|Variable|AZURE_ENV_NAME|Yes|The name of the Azure environment you want to deploy to, such as `copilot-usage-advanced-dashboard-dev`.|
|Variable|AZURE_LOCATION|Yes|The Azure location you want to deploy to, such as `eastus`, `westus`, etc.|
|Variable|AZURE_RESOURCE_GROUP|Yes|The name of the resource group you want to deploy to.|
|Secret|GH_PAT|Yes|This is your GitHub Personal Access Token.|
|Variable|GH_ORGANIZATION_SLUGS|Yes|This is your GitHub Organization name. This can be a comma-separated list of orgs if you want to index multiple orgs.|
|Variable|GRAFANA_USERNAME|Yes/No|The username for Grafana.|
|Secret|GRAFANA_PASSWORD|Yes/No|The password for Grafana.|
|Variable|AZURE_CLIENT_ID|Yes|The Client ID of the identity you want to use to deploy the application.|
|Variable|AZURE_SUBSCRIPTION_ID|Yes|The GUID for the subscription you want to deploy to.|
|Variable|AZURE_TENANT_ID|Yes|The Azure Tenant ID of the identity you want to use to deploy the application.|
|Secret|AZURE_USER_PRINCIPAL_ID|Yes|The Object ID of a user you want to grant access to to the Azure Key Vault.|
|Secret|AZURE_AUTHENTICATION_CLIENT_ID|No|The Client ID of the Azure AD application.|
|Variable|AZURE_AUTHENTICATION_ENABLED|No|Enable Entra ID Single-Sign On (SSO) authentication.|
|Variable|AZURE_AUTHENTICATION_OPEN_ID_ISSUER|No|The OpenID Connect issuer URL for Azure AD.|

---

## Azure Resource Creation Credentials

You need to set up the Azure Credentials secret in the GitHub Secrets at the Repository level before you do anything else.

See [https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/deploy-github-actions](https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/deploy-github-actions) for more info.

You will need to create the variables AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_SUBSCRIPTION_ID from these credentials.

---

## GitHub Action

The GitHub Actions pipeline uses the `azure-dev.yml` file located in the `.github/workflows` folder. Once the secrets and variables are set up correctly, the pipeline will deploy the application.

If you want this to update every time you push to the main branch, uncomment the `push` section in the [.github/workflows/azure-dev.yml](../.github/workflows/azure-dev.yml) file.

---

## GitHub Sample Commands to set variables and secrets

``` bash
gh auth login

gh variable set AZURE_ENV_NAME -b 'copilot-usage-advanced-dashboard-dev'
gh variable set AZURE_RESOURCE_GROUP -b 'rg-copilot-usage-advanced-dashboard-dev'
gh variable set AZURE_LOCATION -b 'eastus'

gh secret set GH_PAT -b '<secretValue>'
gh variable set GH_ORGANIZATION_SLUGS -b '<your-slug-or-slugs>'
gh variable set GRAFANA_USERNAME -b 'admin'
gh secret set GRAFANA_PASSWORD -b '<secretValue>'

gh variable set AZURE_CLIENT_ID -b '<variableValue>'
gh variable set AZURE_SUBSCRIPTION_ID -b '<variableValue>'
gh variable set AZURE_TENANT_ID -b '<variableValue>'

gh secret set AZURE_USER_PRINCIPAL_ID -b '<optionalSecretValue>'
gh secret set AZURE_AUTHENTICATION_CLIENT_ID -b '<optionalSecretValue>'
gh variable set AZURE_AUTHENTICATION_ENABLED -b '<optionalVariableValue>'
gh variable set AZURE_AUTHENTICATION_OPEN_ID_ISSUER -b '<optionalVariableValue>'

```

---

[Home](../README.md#deployment)
