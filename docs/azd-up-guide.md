# Deploying with Azure Developer CLI (`azd up`)

This guide walks you through deploying the Copilot Usage Advanced Dashboard to Azure Container Apps from your local workstation using a single `azd up` command.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1 — Clone the Repository](#step-1--clone-the-repository)
- [Step 2 — Install Required Tools](#step-2--install-required-tools)
- [Step 3 — Log In to Azure](#step-3--log-in-to-azure)
- [Step 4 — Create an azd Environment](#step-4--create-an-azd-environment)
- [Step 5 — Set Required Variables](#step-5--set-required-variables)
- [Step 6 — Deploy with `azd up`](#step-6--deploy-with-azd-up)
- [Step 7 — Access the Dashboard](#step-7--access-the-dashboard)
- [Updating an Existing Deployment](#updating-an-existing-deployment)
- [Tearing Down the Environment](#tearing-down-the-environment)
- [Troubleshooting](#troubleshooting)
- [Environment Variable Reference](#environment-variable-reference)

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Azure Subscription** | Owner or Contributor access required |
| **GitHub PAT** | Token with `manage_billing:copilot`, `read:enterprise`, and `read:org` scopes. [Create one here.](https://github.com/settings/tokens) |
| **GitHub Organization Slug** | The short name of your GitHub org (e.g. `myorg`) |

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/lluppesms/copilot-usage-advanced-dashboard.git
cd copilot-usage-advanced-dashboard
```

---

## Step 2 — Install Required Tools

### Azure Developer CLI (`azd`)

**Windows (winget)**
```powershell
winget install Microsoft.Azd
```

**macOS (Homebrew)**
```bash
brew tap azure/azd && brew install azd
```

**Linux**
```bash
curl -fsSL https://aka.ms/install-azd.sh | bash
```

> Full installation instructions: <https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd>

### Azure CLI (`az`)

The post-deploy scripts require the Azure CLI.

**Windows (winget)**
```powershell
winget install Microsoft.AzureCLI
```

**macOS (Homebrew)**
```bash
brew update && brew install azure-cli
```

**Linux**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

> Full installation instructions: <https://learn.microsoft.com/cli/azure/install-azure-cli>

---

## Step 3 — Log In to Azure

```bash
# Log in to the Azure Developer CLI (opens browser)
azd auth login

# Log in to the Azure CLI (needed for post-deploy scripts)
az login
```

---

## Step 4 — Create an azd Environment

An `azd` environment holds your configuration and deployment state. Choose a short, descriptive name (e.g. `cpilot-prod`, `my-dashboard`).

```bash
azd env new <environment-name>
```

You will be prompted to select your **Azure Subscription** and **Azure Region**.

> **Tip:** The environment name is used as part of Azure resource names, so keep it under 20 characters and use only letters, numbers, and hyphens.  Example: `copilot-prod`

---

## Step 5 — Set Required Variables

`azd up` will fail if the required variables are not set. Run the following commands to configure your environment:

### Required

```bash
# GitHub Personal Access Token
azd env set GITHUB_PAT "ghp_your_token_here"

# GitHub Organization slug(s) — comma-separated for multiple orgs
azd env set GITHUB_ORGANIZATION_SLUGS "your-org-name"
```

> **Multiple orgs example:** `azd env set GITHUB_ORGANIZATION_SLUGS "org1,org2"`
>
> **Copilot Standalone example:** `azd env set GITHUB_ORGANIZATION_SLUGS "standalone:your-standalone-slug"`

### Optional (Grafana credentials)

If you do not set these, the default credentials (`admin` / `copilot`) will be used.

```bash
azd env set GRAFANA_USERNAME "admin"
azd env set GRAFANA_PASSWORD "a-secure-password"
```

### Optional (Azure AD Authentication for Grafana)

To enable Azure AD login on the Grafana endpoint, set:

```bash
azd env set AZURE_AUTHENTICATION_ENABLED "true"
azd env set AZURE_AUTHENTICATION_CLIENT_ID "<your-app-registration-client-id>"
azd env set AZURE_AUTHENTICATION_OPEN_ID_ISSUER "https://login.microsoftonline.com/<your-tenant-id>"
```

---

## Step 6 — Deploy with `azd up`

```bash
azd up
```

This single command will:

1. **Pre-provision validation** — Check that required environment variables are set and print helpful guidance if any are missing.
2. **Provision infrastructure** — Deploy all Azure resources using the Bicep templates in `infra/`:
   - Azure Container Apps environment (with D8 workload profile)
   - Azure Container Registry
   - Azure Key Vault (for secrets)
   - Azure Storage Account (NFS file shares for Elasticsearch and Grafana data)
   - Log Analytics workspace and Application Insights
   - Virtual Network
   - User-assigned Managed Identity
3. **Build and deploy containers** — Build the `elastic-search` and `grafana` container images remotely via ACR and deploy them as Container Apps.
4. **Post-deploy jobs** — Build and start the `update-grafana` and `cpuad-updater` Container App Jobs, which seed the Grafana dashboards and begin fetching Copilot metrics from the GitHub APIs.

> ⏱ The full deployment typically takes **15–25 minutes** on first run.

---

## Step 7 — Access the Dashboard

When `azd up` completes, the Grafana URL is printed to the console. You can also retrieve it at any time with:

```bash
azd env get-values | grep GRAFANA_DASHBOARD_URL
```

Open the URL in your browser and log in with the Grafana credentials you configured (or the defaults `admin` / `copilot`).

> **Note:** It takes up to one hour for Copilot metrics data to appear in the dashboards because the `cpuad-updater` job runs on an hourly schedule. You can trigger it immediately by running:
>
> ```bash
> # Linux/macOS
> ./scripts/deploy-azure-container-app-job-cpuad-updater.sh
>
> # Windows
> ./scripts/Deploy-AzureContainerAppJob-CpuAdUpdater.ps1
> ```

---

## Updating an Existing Deployment

To update infrastructure or redeploy application code after making changes:

```bash
azd up
```

Or run the individual phases separately:

```bash
azd provision   # Re-apply Bicep infrastructure changes only
azd deploy      # Rebuild and redeploy container images only
```

---

## Tearing Down the Environment

To delete all Azure resources created by this deployment:

```bash
azd down
```

> ⚠️ This permanently deletes all resources including Elasticsearch data. Export any dashboards or data you need before running this command.

---

## Troubleshooting

### Pre-provision validation fails

The `scripts/preprovision.sh` (or `scripts/Preprovision.ps1` on Windows) script runs before provisioning and will print clear error messages for any missing required variables. Follow the instructions in the output to set the missing values, then re-run `azd up`.

### "Insufficient permissions" during provisioning

Ensure your Azure account has **Owner** or **Contributor** role on the target subscription or resource group. The Bicep templates create role assignments, which requires Owner-level access.

If you cannot grant Owner access, set `AZURE_ROLE_ASSIGNMENTS=false` to skip role assignments:

```bash
azd env set AZURE_ROLE_ASSIGNMENTS false
```

### Post-deploy scripts fail

The post-deploy scripts require the Azure CLI (`az`) to be installed and authenticated. Run `az login` if you have not done so, then re-run:

```bash
# Re-run post-deploy hooks only
azd hooks run postdeploy
```

### Container App Jobs not starting

Verify the Container Registry has the images by checking:

```bash
az acr repository list --name $(azd env get-values | grep AZURE_CONTAINER_REGISTRY_NAME | cut -d= -f2 | tr -d '"')
```

---

## Environment Variable Reference

| Variable | Required | Description | Default |
|---|---|---|---|
| `GITHUB_PAT` | ✅ Yes | GitHub Personal Access Token | — |
| `GITHUB_ORGANIZATION_SLUGS` | ✅ Yes | Comma-separated org slug(s) | — |
| `GRAFANA_USERNAME` | No | Grafana admin username | `admin` |
| `GRAFANA_PASSWORD` | No | Grafana admin password | `copilot` |
| `AZURE_ROLE_ASSIGNMENTS` | No | Create role assignments during provisioning | `true` |
| `AZURE_AUTHENTICATION_ENABLED` | No | Enable Azure AD auth on Grafana | `false` |
| `AZURE_AUTHENTICATION_CLIENT_ID` | No | Azure AD app registration client ID | — |
| `AZURE_AUTHENTICATION_OPEN_ID_ISSUER` | No | OpenID Connect issuer URL | — |
| `ASSIGN_PERMISSIONS_TO_PRINCIPAL` | No | Grant permissions to the deploying principal | `true` |
