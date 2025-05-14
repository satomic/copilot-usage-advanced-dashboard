

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

1. **Optional*** Run the following commands to set the Grafana credentials. Note that not setting this values results in the deployment script generating credentials.

   ```shell
   azd env set GRAFANA_USERNAME ...
   azd env set GRAFANA_PASSWORD ...
   ```

1. Run the following command to deploy the application.

   ```shell
   azd up
   ```
   
1. After the deployment is complete, you can access the application using the URL provided in the output.

1. The username & password for the Grafana dashboard can be found in the Key Vault. Note that these are not secure credentials and should be changed.