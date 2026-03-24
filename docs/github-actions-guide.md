# Deploy with a GitHub Action

When setting up a deployment you will need to set the following variables and secrets in your GitHub environment manually:

|**Secrets**|**Description**|
|-|-|
|AZURE_USER_PRINCIPAL_ID|The Object ID of a user you want to grant access to to the Azure Key Vault.|
|AZURE_AUTHENTICATION_CLIENT_ID|The Client ID of the Azure AD application.|
|GH_PAT|This is your GitHub Personal Access Token.|
|GRAFANA_PASSWORD|The password for Grafana.|

|**Variables**|**Description**|
|-|-|
|AZURE_CLIENT_ID|The Client ID of the identity you want to use to deploy the application.|
|AZURE_ENV_NAME|The name of the Azure environment you want to deploy to, such as `copilot-usage-advanced-dashboard-dev`.|
|AZURE_LOCATION|The Azure location you want to deploy to, such as `eastus`, `westus`, etc.|
|AZURE_RESOURCE_GROUP|The name of the resource group you want to deploy to.|
|AZURE_SUBSCRIPTION_ID|The GUID for the subscription you want to deploy to.|
|AZURE_TENANT_ID|The Azure Tenant ID of the identity you want to use to deploy the application.|
|GH_ORGANIZATION_SLUGS|This is your GitHub Organization name. This can be a comma-separated list of orgs if you want to index multiple orgs.|
|AZURE_AUTHENTICATION_ENABLED|Enable Entra ID Single-Sign On (SSO) authentication.|
|AZURE_AUTHENTICATION_OPEN_ID_ISSUER|The OpenID Connect issuer URL for Azure AD.|
|GRAFANA_USERNAME|The username for Grafana.|

---

## Azure Resource Creation Credentials

You need to set up the Azure Credentials secret in the GitHub Secrets at the Repository level before you do anything else.

See [https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/deploy-github-actions](https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/deploy-github-actions) for more info.

You will need to create the variables AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_SUBSCRIPTION_ID from these credentials.

---

## GitHub Action

The GitHub Actions pipeline uses the `azure-dev.yml` file located in the `.github/workflows` folder. Once the secrets and variables are set up correctly, the pipeline will deploy the application.

If you want this to update every time you push to the main branch, uncomment the `push` section in the [../.github/workflows/azure-dev.yml](.github/workflows/azure-dev.yml) file.

---

## GitHub Sample Commands to set variables and secrets

``` bash
gh auth login

gh secret set GH_PAT -b '<value>'

gh secret set AZURE_USER_PRINCIPAL_ID -b '<value>'
gh secret set AZURE_AUTHENTICATION_CLIENT_ID -b '<value>'

gh secret set GRAFANA_PASSWORD -b '<value>'

gh variable set AZURE_CLIENT_ID -b '<value>'
gh variable set AZURE_SUBSCRIPTION_ID -b '<value>'
gh variable set AZURE_TENANT_ID -b '<value>'

gh variable set AZURE_ENV_NAME -b '<value>'
gh variable set AZURE_LOCATION -b '<value>'
gh variable set AZURE_RESOURCE_GROUP -b '<value>'

gh variable set GH_ORGANIZATION_SLUGS -b '<value>'

gh variable set GRAFANA_USERNAME -b '<value>'

gh variable set AZURE_AUTHENTICATION_ENABLED -b '<value>'
gh variable set AZURE_AUTHENTICATION_OPEN_ID_ISSUER -b '<value>'

```

---

[Home](../README.md#deployment)
