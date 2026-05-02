# Copilot Usage Advanced Dashboard Tutorial

## 🚀 Quick Start - Run Locally (5 Minutes)

### Prerequisites
- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- GitHub Personal Access Token with `manage_billing:copilot` scope ([Create Token](https://github.com/settings/tokens))
- Your GitHub Organization/Enterprise slug

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/satomic/copilot-usage-advanced-dashboard.git
cd copilot-usage-advanced-dashboard
```

2. **Configure environment**
```bash
cp .env.template .env
# Edit .env file with your GitHub PAT and organization slug
```

Minimal required configuration:
```env
GITHUB_PAT=ghp_your_token_here
ORGANIZATION_SLUGS=your-org-name
```

3. **Start the dashboard**
```bash
docker-compose up -d
```

4. **Access Grafana**
- URL: **http://localhost:8080**
- Username: `admin`
- Password: `copilot`
- ✨ Dashboard loads automatically - no manual import needed!

### What Happens Automatically
✅ Elasticsearch starts and creates 7 indexes  
✅ Grafana starts with pre-configured datasources  
✅ Dashboard provisions automatically from `/grafana-provisioning/dashboards/`  
✅ `cpuad-updater` fetches data from 5 GitHub APIs every hour  
✅ User metrics populate in "User Metrics" row (9 panels)  
✅ System self-heals if any container crashes  

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|  
| `GITHUB_PAT` | ✅ Yes | GitHub Personal Access Token | - |
| `ORGANIZATION_SLUGS` | ✅ Yes | Comma-separated org slugs | - |
| `ELASTICSEARCH_URL` | No | Elasticsearch endpoint | `http://elasticsearch:9200` |
| `EXECUTION_INTERVAL_HOURS` | No | Data fetch frequency (hours) | `1` |
| `INDEX_USER_METRICS` | No | User metrics index name | `copilot_user_metrics` |
| `INDEX_USER_ADOPTION` | No | Adoption leaderboard index | `copilot_user_adoption` |

---

[Home](../README.md)