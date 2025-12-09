# Deployment Options for Copilot Usage Advanced Dashboard

## Option A: Docker on Linux (Windows or Linux with Docker Desktop)

### Objective
Deploy the entire dashboard stack locally or on a private Linux host to prove functionality quickly.

### Prerequisites
- Docker Desktop (Windows/macOS) or Docker Engine on Linux
- Minimum 8 GB RAM, 2 vCPU, 20 GB disk space
- Ports 8080 (Grafana) and 9200 (Elasticsearch) open internally
- Git installed to pull the repo
- GitHub Personal Access Token (PAT) with `manage_billing:copilot` scope
- Organization slug(s) (comma-separated if multiple)

### Setup Steps
1. Clone repository and enter directory:
   ```powershell
   git clone https://github.com/satomic/copilot-usage-advanced-dashboard.git
   cd copilot-usage-advanced-dashboard
   ```
2. Copy environment template and edit:
   ```powershell
   copy .env.template .env
   ```
   Update `.env` with:
   - `GITHUB_PAT=ghp_<token>`
   - `ORGANIZATION_SLUGS=demo-org`
   - Optional: `EXECUTION_INTERVAL_HOURS=1`
3. Start services:
   ```powershell
   docker-compose up -d --build
   ```
4. Validate:
   - `docker ps` shows `elasticsearch`, `grafana`, `cpuad-updater`, `init-grafana`
   - Grafana accessible at http://localhost:8080 (admin/copilot)
   - AMD logs: `docker logs cpuad-updater --tail 20`

### What Happens
- Elasticsearch stores 7 indexes including `copilot_user_metrics`
- Grafana provisions dashboard automatically
- `cpuad-updater` runs hourly, fetching GitHub APIs and storing results
- Data persists even if Grafana restarts

### Customer Benefits
- Quick proof of concept and local demo
- Full control over data and environment
- Can be converted to production (move to Linux server or VM)

---

## Option B: Azure Container Apps (Production ready)

### Objective
Deploy the dashboard to Azure Container Apps for managed hosting, autoscaling, and secure access.

### Prerequisites
- Azure subscription with Owner or Contributor rights
- Azure CLI (`az`) and Azure Developer CLI (`azd`) installed
- GitHub PAT with `manage_billing:copilot`
- Desired Azure region (e.g., eastus)
- Resource group name

### Setup Steps
1. Clone repo and initialize environment:
   ```powershell
   git clone https://github.com/satomic/copilot-usage-advanced-dashboard.git
   cd copilot-usage-advanced-dashboard
   az login
   azd auth login
   azd env new copilot-dashboard-prod
   ```
2. Set required variables:
   ```powershell
   azd env set GITHUB_PAT "ghp_<token>"
   azd env set ORGANIZATION_SLUGS "your-org"
   azd env set EXECUTION_INTERVAL_HOURS "1"
   ```
3. Deploy to Azure Container Apps (creates Container Apps, connected storage, environment):
   ```powershell
   azd up
   ```
4. Capture Grafana URL from deployment output and log in via admin/copilot.

### Architecture in Azure
- Azure Container Apps environment hosts:
  - `cpuad-updater` job/container (hourly run)
  - `grafana` container app (frontend)
  - `elasticsearch` container app (data storage)
- Azure Storage Account attached for Grafana data + ES logs
- Log Analytics workspace for monitoring
- Optional Key Vault for secrets

### Operational Notes
- `cpuad-updater` runs continuously or as scheduled job (replica scaling)
- Logs accessible via `az containerapp logs show`
- Use Azure Container Apps revisioning for deployments
- Secure Grafana: configure private endpoint or restrict to allowed IPs

### Benefits for Customer
- Managed infra: auto-scaling, SLA-backed
- Standardized deployment with IaC (`infra/` Bicep modules)
- Seamless upgrade path via `azd up`
- Centralized monitoring and RBAC

### Cost Considerations
- Container Apps consumption plus storage and log data (~$50-100/mo)
- Use Azure Cost Management to cap spend

---

## Supporting Materials
- Architecture diagram: `image/architecture.drawio.png`
- Dashboard screenshots: `image/user-metrics-summary.png`, `image/user-metrics-charts.png`
- README documentation: see `README.md` sections 1-8 for usage guidance

---

## Next Steps for Client
1. Choose deployment option (Docker for POC, Azure for production)
2. Prepare GitHub PAT (`manage_billing:copilot`)
3. Provide organization slug(s)
4. Deploy environment and verify Grafana access
5. Share viewer credentials or connect through secure tunnel as needed
6. Schedule knowledge transfer (dashboard walkthrough, automation, maintenance)
