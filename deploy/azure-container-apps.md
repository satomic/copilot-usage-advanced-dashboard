

## Architecture diagram

![](/image/architecture.drawio.png)

## Technology stack

Dependent technology stack:

- Azure Container Apps
- Elasticsearch
- Grafana
- Python3


## Deploy in Azure Container Apps
This document describes how to deploy the application in Azure Container Apps using the Azure Developer CLI.

1. Run the following command to set the GitHub credentials in the Azure Developer CLI.

   ```shell
   azd env set GITHUB_PAT ...

   azd env set GITHUB_ORGANIZATION_SLUGS ...
   ```

1. **Optional** Run the following commands to set the Grafana credentials. Note that not setting this values results in the deployment script generating credentials.

   ```shell
   azd env set GRAFANA_USERNAME ...

   azd env set GRAFANA_PASSWORD ...
   ```

1. Run the following command to deploy the application.

   ```shell
   azd up
   ```

1. After the deployment is complete, you can access the application using the URL provided in the output.

1. The username & password for the Grafana dashboard can be found in the Key Vault. Note that the default values (if you didn't specify them or are not using Entra ID auth) are not secure credentials and should be changed.

### Optional: Enable Entra ID SSO for Grafana

The Grafana dashboard only uses the `Viewer` role. This means all users that can sign in can see the same data. If you need more fine-grained access, you should follow this URL to set up Entra ID SSO for Grafana: [Grafana Entra ID SSO](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/azuread/). You can also limit which users can sign in to the Grafana dashboard using [Entra ID groups](https://learn.microsoft.com/en-us/entra/identity-platform/howto-restrict-your-app-to-a-set-of-users)

1. Create an app registration in Entra ID (Azure Active Directory) with the following settings:

   - **Name**: `copilot-usage-advanced-dashboard` (or something similar)
   - **Supported account types**: Accounts in this organizational directory only (Single tenant)
   - **Redirect URI**: Leave this blank for now, you can update it after the deployment.
   - **Overview->Application (client) ID**: Copy this value, you will need it later.
   - **Overview->Directory (tenant) ID**: Copy this value, you will need it later.
   - **Authentication->Implicit grant and hybrid flows**: Check the box for `ID tokens` to enable OpenID Connect authentication.
   - **API permissions**: Add the following delegated API permissions to allow Container Apps to sign-in users.
     - Microsoft Graph
       - `openid`
       - `profile`
       - `offline_access`
       - `User.Read`

1. Run the following command to set the Entra ID tenant ID

   ```shell
   azd env set AZURE_AUTHENTICATION_ENABLED true

   azd env set AZURE_AUTHENTICATION_CLIENT_ID <your-app-registration-client-id>

   azd env set AZURE_AUTHENTICATION_OPEN_ID_ISSUER https://login.microsoftonline.com/<your-tenant-id>
   ```

1. Run the following command to deploy the application.

   ```shell
   azd up
   ```

1. **Optional**: If you enabled Entra ID authentication, you will need to update the Entra ID app registration with values from the deployment.

   - **Authentication->Redirect URI**: Update the app registration with the URL of the Grafana dashboard, e.g., `https://<your-container-app-name>.<location>.azurecontainerapps.io/.auth/login/aad/callback`.
   - **Certificates & secrets->Federated credentials**: Add a new federated credential with the following settings:
     - **Federated credential scenario**: Managed Identity
     - **Select managed identity**: Select the managed identity created for the Container App (look in the Azure portal under the Container App's Identity section to find the name of the managed identity).
     - **Name**: `copilot-usage-advanced-dashboard` (or something similar)

1. After the deployment is complete, you can access the application using the URL provided in the output.
