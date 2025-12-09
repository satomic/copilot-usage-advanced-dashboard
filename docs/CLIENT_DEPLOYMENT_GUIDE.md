# Client Deployment Guide - Copilot Usage Advanced Dashboard

## Overview
This guide provides step-by-step instructions for deploying the Copilot Usage Advanced Dashboard for your organization. The dashboard visualizes GitHub Copilot usage metrics, adoption rates, and user engagement across your enterprise.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Required Information](#required-information)
3. [Deployment Steps](#deployment-steps)
4. [Configuration](#configuration)
5. [Accessing the Dashboard](#accessing-the-dashboard)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Memory**: Minimum 4GB RAM available for Docker
- **Disk Space**: Minimum 10GB free space
- **Network**: Internet access to pull Docker images and access GitHub API

### GitHub Requirements
- **GitHub Enterprise Cloud** or **GitHub Enterprise Server** account
- **GitHub Personal Access Token (PAT)** with the following scopes:
  - `manage_billing:copilot` - Required to read Copilot usage metrics
  - `read:org` - Required to read organization data
  - `read:user` - Required to read user information
- **Organization Admin Access** - Required to generate the PAT with appropriate permissions

### Technical Skills
- Basic command-line interface (CLI) knowledge
- Understanding of Docker and containerization
- Basic networking concepts (ports, localhost)

---

## Required Information

Before starting the deployment, gather the following information:

### 1. GitHub Organization Details
```
Organization Name: _______________________
GitHub API URL: https://api.github.com (for Cloud) or your Enterprise Server API URL
```

### 2. GitHub Personal Access Token
```
Token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**How to Generate a PAT:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token" → "Generate new token (classic)"
3. Set token name: `Copilot Usage Dashboard`
4. Set expiration: 90 days (or as per your security policy)
5. Select scopes:
   - ✅ `manage_billing:copilot`
   - ✅ `read:org`
   - ✅ `read:user`
6. Click "Generate token" and copy the token immediately

### 3. Grafana Credentials
```
Admin Username: admin (default)
Admin Password: _______________________ (choose a secure password)
```

---

## Deployment Steps

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/vanchaudhary/copilot-usage-advanced-dashboard.git

# Navigate to the project directory
cd copilot-usage-advanced-dashboard
```

### Step 2: Configure Environment Variables

Edit the `docker-compose.yml` file with your organization-specific details:

```bash
# Open docker-compose.yml in your preferred editor
nano docker-compose.yml
# or
vim docker-compose.yml
# or use VS Code, Notepad++, etc.
```

**Required Changes:**

#### 2.1 Update GitHub Configuration (cpuad-updater service)
Locate the `cpuad-updater` service and update:

```yaml
environment:
  GITHUB_ORG: "YOUR_ORG_NAME"              # Replace with your GitHub organization name
  GITHUB_TOKEN: "YOUR_GITHUB_TOKEN"        # Replace with your PAT (ghp_xxx...)
  GITHUB_API_URL: "https://api.github.com" # For Enterprise Server, use your server's API URL
```

**Example:**
```yaml
environment:
  GITHUB_ORG: "acme-corporation"
  GITHUB_TOKEN: "ghp_abc123XYZ789..."
  GITHUB_API_URL: "https://api.github.com"
```

#### 2.2 Update Grafana Password (init-grafana service)
Locate the `init-grafana` service and update:

```yaml
environment:
  GRAFANA_PASSWORD: "YOUR_SECURE_PASSWORD"  # Replace with a strong password
```

**Example:**
```yaml
environment:
  GRAFANA_PASSWORD: "MySecureGrafana2024!"
```

#### 2.3 (Optional) Adjust Resource Limits
If your system has limited resources, you can reduce memory/CPU limits:

```yaml
deploy:
  resources:
    limits:
      memory: 512M  # Reduce from 1G if needed
      cpus: '0.25'  # Reduce from 0.5 if needed
```

### Step 3: Validate Configuration

Before starting, verify your configuration:

```bash
# Check Docker is running
docker --version
docker compose version

# Validate docker-compose.yml syntax
docker compose config
```

### Step 4: Deploy the Stack

```bash
# Pull the required Docker images
docker compose pull

# Start the services in detached mode
docker compose up -d

# Verify all containers are running
docker compose ps
```

**Expected Output:**
```
NAME                                          STATUS    PORTS
copilot-usage-advanced-dashboard-cpuad-updater-1    running   
copilot-usage-advanced-dashboard-elasticsearch-1    running   0.0.0.0:9200->9200/tcp
copilot-usage-advanced-dashboard-grafana-1          running   0.0.0.0:8080->80/tcp
copilot-usage-advanced-dashboard-init-grafana-1     exited (0)
```

**Note:** The `init-grafana` container should exit with status 0 after provisioning Grafana.

### Step 5: Wait for Initial Data Collection

The `cpuad-updater` service fetches data from GitHub API every hour. Wait 5-10 minutes for:
1. Initial data fetch from GitHub API
2. Data indexing in Elasticsearch
3. Grafana dashboard provisioning

**Monitor Progress:**
```bash
# Check cpuad-updater logs
docker compose logs -f cpuad-updater

# Check init-grafana logs
docker compose logs init-grafana

# Check for Elasticsearch indexes
curl -X GET "http://localhost:9200/_cat/indices?v"
```

### Step 6: Verify Deployment

```bash
# Test Elasticsearch is accessible
curl -X GET "http://localhost:9200/_cluster/health?pretty"

# Test Grafana is accessible
curl -I http://localhost:8080

# Check all indexes are created
curl -X GET "http://localhost:9200/_cat/indices/copilot_*?v"
```

---

## Configuration

### Data Refresh Schedule

By default, the dashboard fetches data **every hour**. To adjust:

Edit `docker-compose.yml` under `cpuad-updater` service:

```yaml
environment:
  FETCH_INTERVAL: "3600"  # Change to desired interval in seconds
                          # 3600 = 1 hour
                          # 1800 = 30 minutes
                          # 7200 = 2 hours
```

After changing, restart the service:
```bash
docker compose restart cpuad-updater
```

### Time Zone Configuration

To set the correct timezone for your organization:

```yaml
environment:
  TZ: "America/New_York"  # Change to your timezone
                          # Examples: "Europe/London", "Asia/Tokyo", "Australia/Sydney"
```

### Elasticsearch Retention Policy

By default, all data is retained indefinitely. To set a retention policy:

```bash
# Delete data older than 90 days for usage metrics
curl -X DELETE "http://localhost:9200/copilot_usage_breakdown/_delete_by_query?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"range": {"@timestamp": {"lt": "now-90d"}}}}'
```

Consider setting up a cron job for automatic cleanup.

---

## Accessing the Dashboard

### Grafana Web Interface

1. **Open Browser**: Navigate to `http://localhost:8080`
   - If accessing remotely: `http://<SERVER_IP>:8080`

2. **Login**: 
   - Username: `admin`
   - Password: `<YOUR_SECURE_PASSWORD>` (from docker-compose.yml)

3. **Navigate to Dashboard**:
   - Click "Dashboards" in left sidebar
   - Select "Copilot Usage Advanced Dashboard"

### Dashboard URL Direct Access

```
http://localhost:8080/d/bf59bgj6fjd34c/copilot-usage-advanced-dashboard
```

### Elasticsearch Direct Access (Optional)

For advanced users who want to query data directly:

```
http://localhost:9200
```

**Example Queries:**

```bash
# Get total usage breakdown documents
curl -X GET "http://localhost:9200/copilot_usage_breakdown/_count"

# Get recent user metrics
curl -X GET "http://localhost:9200/copilot_user_metrics/_search?size=10&pretty"

# Get seat assignments
curl -X GET "http://localhost:9200/copilot_seat_assignments/_search?pretty"
```

---

## Troubleshooting

### Issue 1: Containers Not Starting

**Symptoms:**
- `docker compose ps` shows containers as "Exit 1" or "Restarting"

**Solutions:**

```bash
# Check logs for errors
docker compose logs elasticsearch
docker compose logs grafana
docker compose logs cpuad-updater

# Common fixes:
# 1. Increase Docker memory limit (Docker Desktop → Settings → Resources)
# 2. Check port conflicts (8080, 9200)
netstat -ano | findstr "8080"
netstat -ano | findstr "9200"

# 3. Restart Docker service
# Windows: Restart Docker Desktop
# Linux: sudo systemctl restart docker
```

### Issue 2: No Data in Grafana Panels

**Symptoms:**
- Dashboard loads but panels show "No data"

**Solutions:**

```bash
# 1. Verify GitHub token has correct permissions
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
     https://api.github.com/orgs/YOUR_ORG/copilot/usage

# 2. Check cpuad-updater is fetching data
docker compose logs cpuad-updater | grep -i "success\|error"

# 3. Verify Elasticsearch indexes exist
curl -X GET "http://localhost:9200/_cat/indices/copilot_*?v"

# 4. Check data exists in indexes
curl -X GET "http://localhost:9200/copilot_usage_breakdown/_count"

# 5. Wait 5-10 minutes for initial data fetch
```

### Issue 3: Grafana Login Failed

**Symptoms:**
- Cannot login with admin credentials

**Solutions:**

```bash
# 1. Verify password in docker-compose.yml
grep "GRAFANA_PASSWORD" docker-compose.yml

# 2. Reset Grafana admin password
docker compose exec grafana grafana-cli admin reset-admin-password NEW_PASSWORD

# 3. Restart Grafana
docker compose restart grafana
```

### Issue 4: GitHub API Rate Limit

**Symptoms:**
- Logs show "API rate limit exceeded"

**Solutions:**

```bash
# 1. Check your current rate limit
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
     https://api.github.com/rate_limit

# 2. Increase fetch interval to reduce API calls
# Edit docker-compose.yml:
FETCH_INTERVAL: "7200"  # Change to 2 hours

# 3. Use a GitHub App instead of PAT (higher rate limits)
```

### Issue 5: Port Already in Use

**Symptoms:**
- Error: "bind: address already in use"

**Solutions:**

```bash
# Find process using the port
# Windows:
netstat -ano | findstr "8080"
# Linux/Mac:
lsof -i :8080

# Option 1: Stop the conflicting service
# Option 2: Change port in docker-compose.yml
ports:
  - "8090:80"  # Change 8080 to 8090 or any available port
```

### Issue 6: Elasticsearch Yellow/Red Status

**Symptoms:**
- Elasticsearch cluster health is yellow or red

**Solutions:**

```bash
# Check cluster health
curl -X GET "http://localhost:9200/_cluster/health?pretty"

# For single-node setup, yellow status is normal
# Set replicas to 0 for all indexes
curl -X PUT "http://localhost:9200/copilot_*/_settings" \
  -H 'Content-Type: application/json' \
  -d '{"index": {"number_of_replicas": 0}}'
```

### Issue 7: Dashboard Panels Show Wrong Time Range

**Symptoms:**
- Panels show "No data" for specific time ranges

**Solutions:**

1. Check time picker in top-right (default: Last 30 days)
2. Verify data exists for selected time range:
   ```bash
   curl -X GET "http://localhost:9200/copilot_usage_breakdown/_search?pretty" \
     -H 'Content-Type: application/json' \
     -d '{"query": {"match_all": {}}, "sort": [{"@timestamp": "desc"}], "size": 1}'
   ```
3. Adjust time range to include existing data

### Getting Help

If issues persist:

1. **Collect Diagnostic Information:**
   ```bash
   # Save all logs
   docker compose logs > logs.txt
   
   # Save container status
   docker compose ps > status.txt
   
   # Save Elasticsearch indexes
   curl -X GET "http://localhost:9200/_cat/indices?v" > indexes.txt
   ```

2. **Check GitHub Issues**: https://github.com/vanchaudhary/copilot-usage-advanced-dashboard/issues

3. **Contact Support**: Provide logs and diagnostic information

---

## Maintenance

### Regular Tasks

#### Daily
- Monitor disk space usage
  ```bash
  docker system df
  ```

#### Weekly
- Check container health
  ```bash
  docker compose ps
  docker compose logs --tail=100 cpuad-updater
  ```

#### Monthly
- Update Docker images
  ```bash
  docker compose pull
  docker compose up -d
  ```
- Rotate GitHub PAT (if expiring)
- Review Elasticsearch storage usage

### Backup Procedures

#### Backup Grafana Dashboards
```bash
# Export current dashboard
curl -u admin:YOUR_PASSWORD \
  "http://localhost:8080/api/dashboards/uid/bf59bgj6fjd34c" \
  > backup-dashboard-$(date +%Y%m%d).json
```

#### Backup Elasticsearch Data
```bash
# Create snapshot repository (one-time setup)
curl -X PUT "http://localhost:9200/_snapshot/backup" \
  -H 'Content-Type: application/json' \
  -d '{"type": "fs", "settings": {"location": "/usr/share/elasticsearch/backup"}}'

# Create snapshot
curl -X PUT "http://localhost:9200/_snapshot/backup/snapshot_$(date +%Y%m%d)?wait_for_completion=true"
```

### Updating the Stack

```bash
# Pull latest changes from repository
git pull origin main

# Rebuild and restart containers
docker compose down
docker compose pull
docker compose up -d

# Verify update
docker compose ps
docker compose logs init-grafana
```

### Scaling Considerations

For large organizations (>1000 Copilot users):

1. **Increase Elasticsearch Memory:**
   ```yaml
   elasticsearch:
     deploy:
       resources:
         limits:
           memory: 2G  # Increase from 1G
   ```

2. **Adjust Fetch Interval:**
   ```yaml
   cpuad-updater:
     environment:
       FETCH_INTERVAL: "3600"  # Keep at 1 hour or increase
   ```

3. **Consider External Elasticsearch:**
   - Use managed Elasticsearch service (AWS OpenSearch, Elastic Cloud)
   - Update ELASTICSEARCH_URL in docker-compose.yml

---

## Security Best Practices

### 1. GitHub Token Security
- ✅ Use tokens with minimal required scopes
- ✅ Set token expiration (90 days maximum)
- ✅ Rotate tokens regularly
- ✅ Store tokens in environment variables, not in code
- ❌ Never commit tokens to Git repositories

### 2. Grafana Security
- ✅ Use strong admin password (12+ characters, mixed case, numbers, symbols)
- ✅ Change default admin password immediately after deployment
- ✅ Enable HTTPS if exposing Grafana to internet
- ✅ Restrict Grafana port (8080) to internal network only
- ✅ Create read-only users for dashboard viewers

### 3. Network Security
- ✅ Use firewall rules to restrict access to ports 8080 and 9200
- ✅ Consider using reverse proxy (nginx) with SSL/TLS
- ✅ Use VPN for remote access instead of exposing ports publicly
- ❌ Never expose Elasticsearch (port 9200) to public internet

### 4. Docker Security
- ✅ Keep Docker and Docker Compose updated
- ✅ Use official Docker images only
- ✅ Regularly update images to get security patches
- ✅ Set resource limits to prevent DoS attacks

---

## Costs and Licensing

### Docker Resources
- **Free**: Docker Desktop for personal use
- **Paid**: Docker Desktop for organizations with >250 employees

### GitHub API
- **Free**: Included with GitHub Enterprise Cloud/Server
- **Rate Limits**: 5,000 requests/hour with PAT

### Infrastructure
- **Self-Hosted**: Only server/VM costs
- **Estimated Resources**: 4GB RAM, 2 CPU cores, 10GB disk

---

## FAQ

**Q: How long does initial setup take?**  
A: 10-15 minutes for configuration, 5-10 minutes for first data fetch.

**Q: Can I deploy this on cloud platforms (AWS, Azure, GCP)?**  
A: Yes! See [deployment-options.md](./deployment-options.md) for cloud deployment guides.

**Q: How much data will be stored?**  
A: Approximately 10-50MB per day depending on organization size. For 1 year: ~4-20GB.

**Q: Can I customize the dashboard?**  
A: Yes! Edit `src/cpuad-updater/grafana/dashboard-template.json` and follow instructions in [GRAFANA_DASHBOARD_LOADING.md](../GRAFANA_DASHBOARD_LOADING.md).

**Q: Is internet access required after deployment?**  
A: Yes, the dashboard needs continuous access to GitHub API to fetch updated metrics.

**Q: Can multiple people access the dashboard simultaneously?**  
A: Yes, Grafana supports multiple concurrent users viewing the dashboard.

**Q: What happens if GitHub API is down?**  
A: The dashboard will continue displaying existing data. New data will be fetched once API is available.

**Q: Can I export dashboard data to CSV/PDF?**  
A: Yes, Grafana supports exporting panels as CSV and dashboards as PDF.

---

## Next Steps

After successful deployment:

1. ✅ **Verify Data**: Check all panels are showing data after 10 minutes
2. ✅ **Share Access**: Create additional Grafana users for your team
3. ✅ **Set Time Range**: Adjust dashboard time picker to your preferred range
4. ✅ **Schedule Review**: Set up weekly review meetings to analyze metrics
5. ✅ **Plan Actions**: Use insights to drive Copilot adoption in your organization

## Support

For questions or issues:
- **GitHub Issues**: https://github.com/vanchaudhary/copilot-usage-advanced-dashboard/issues
- **Documentation**: See `docs/` folder for additional guides
- **Demo Guide**: See generated demo documentation for panel explanations

---

**Version**: 1.0  
**Last Updated**: December 2025  
**Compatibility**: Docker 20.10+, Docker Compose 2.0+, GitHub Enterprise Cloud/Server





Copilot Usage Advanced Dashboard - Complete Client Demo Guide


- Overview


This dashboard provides comprehensive analytics on GitHub Copilot usage across your organization, pulling data from 5 different GitHub APIs and displaying it in 8 major sections.

Dashboard Variables (Filters at Top)

These filters dynamically control what data is displayed across all panels:

1.Organization - Select which 2.GitHub organization(s) to view
3.Team - Filter by specific team(s) within the organization
4.Language - Filter by programming language (Python, Java, etc.)
5.Editor - Filter by code editor (VS Code, JetBrains, etc.)
6.Model - Filter by Copilot model used for code completion
7.Chat Model - Filter by model used for Copilot Chat
8.Team for Users - Filter user-specific data by team membership
9.User - Filter to specific users

Time Range: Default "Last 30 days" (adjustable in top-right corner)



Row 1: Organization Overview
**API Used:** GET /orgs/{org}/copilot/usage (aggregated from team metrics)

**Purpose:** Executive-level summary providing high-level KPIs and trends across the entire organization. This is your "at-a-glance" health check showing overall Copilot effectiveness, engagement volume, and adoption patterns. Use this row to answer: "Is Copilot delivering value across our organization?"

**Key Metrics:** Acceptance rates, total suggestions/acceptances, lines of code impact, user activity trends

**Target Audience:** Leadership, executives, program managers making ROI decisions

---

Panels:
1. Acceptance Rate Average (50%)

Formula: total_acceptances / total_suggestions × 100
Shows how often developers accept Copilot's code suggestions
50% means half of all suggestions are accepted

2. Cumulative Number of Acceptances (12)
Total count of accepted Copilot suggestions across all users/teams
Direct sum from API

3. Cumulative Number of Suggestions (24)
Total suggestions generated by Copilot
Shows Copilot engagement volume

4. Cumulative Number of Lines of Code Accepted (12)
 Total lines of code accepted from Copilot
Measures productivity impact

5. Acceptance Rate (%) - Time Series
Daily acceptance rate trends over time
Visualizes adoption patterns

6. Total Active Users - Bar Chart

 Daily active user count by date
Shows 4 active users on specific days (11/03, 11/24-11/26)

7. Total Suggestions & Acceptances Count - Time Series

Dual-line chart comparing suggestions (blue) vs acceptances (purple)
Peak activity on 11/03 (~12 suggestions, 4 acceptances)

8. Total Lines Suggested & Accepted - Time Series
Similar pattern showing lines suggested vs accepted
Correlates with suggestion patterns


Row 2: User Metrics
**API Used:** GET /orgs/{org}/copilot/metrics/user (28-day rolling window)

**Purpose:** Individual developer performance analysis and adoption leaderboard. Identifies champions vs. users needing support. This row answers: "Who are our Copilot power users and who needs training?" Use this to drive targeted enablement programs and recognize top adopters.

**Key Metrics:** Per-user suggestions/acceptances, adoption scores, detailed activity breakdown, Top 10 leaderboard

**Target Audience:** Engineering managers, team leads, DevOps, training coordinators

---

Panels:
1. Total Users (2)

Count of users with Copilot activity in selected time range
neildcruz_octocps, sombaner_octocps

2. Total Suggestions (57)

Sum of all code suggestions across all users

3. Total Acceptances (3)

Sum of accepted suggestions


4. Acceptance Rate (9.68%, 184%, 27.2%)

-Multiple acceptance rate calculations
-Showing different time periods or metrics


5. Detailed User Analytics - Table

Comprehensive per-user breakdown:
User: Username
User Initiated Interactions: Manual triggers (14, 4)
Code Suggestions Generated: Suggestions count (51, 6)
Code Suggestions Accepted: Acceptances (2, 1)
Average LOC Suggested: Avg lines per suggestion (82, 12.5)
Average LOC Added: Avg lines accepted (522, 291)
Agent Usage: Copilot Agent interactions (2, 1)
Chat Usage: Copilot Chat usage (2, 1)

6. Daily Active Users - Time Series
-Shows unique active users per day
-Activity spikes on 11/03, 11/24-11/26

7. Code Generation & Acceptance Activity - Time Series

Dual-line chart showing generation vs acceptance trends

Green: code_generation_activity_count
Yellow: code_acceptance_activity_count

8. Top 10 Copilot Users - Horizontal Bar Chart ⭐

**THIS IS YOUR FIXED PANEL!**

**API/Index:** `copilot_user_adoption` (calculated adoption scores)

**Aggregation Query:**
- **Field:** `user_login` (direct keyword field, not `.keyword`)
- **Metric:** `max(adoption_pct)` - Maximum adoption percentage per user
- **Datasource:** `elasticsearch-user-adoption` (UID: ff57sd6383egwa)

**How Adoption % is Calculated:**

The `adoption_pct` is a **composite score** calculated from multiple user engagement metrics:

1. **Base Score (5 normalized signals @ 20% weight each):**
   - **Volume** (20%): Total Copilot interactions
   - **Interactions per Day** (20%): Daily activity rate
   - **Acceptance Rate** (20%): % of suggestions accepted
   - **Average Lines Added** (20%): Lines of code added per session
   - **Feature Breadth** (20%): Usage across Agent + Chat features

2. **Consistency Bonus (up to 10% boost):**
   - Based on `active_days` / `max_active_days` across all users
   - Rewards users with consistent daily usage

3. **Final Calculation:**
   - `adoption_score = base_score × (1 + consistency_bonus)`
   - `adoption_pct = (adoption_score / max_score) × 100`
   - Normalized so top user = 100%

**Example Results:**
- `neildcruz_octocps`: 100% (highest composite score - top adopter)
- `sombaner_octocps`: 24.2% (lower engagement across metrics)

**Color Coding:**
- Red (0-40%): Needs attention
- Orange (40-60%): Moderate usage
- Yellow (60-80%): Good usage
- Green (80-95%): Excellent
- Blue (95-100%): Top adopter


Row 3: Teams
**API Used:** Aggregated from GET /orgs/{org}/team/{team_slug}/copilot/usage

**Purpose:** Team-level performance comparison to identify which teams are successfully adopting Copilot vs. those needing support. Answers: "Which teams are getting the most value?" and "Where should we focus our enablement efforts?" Useful for creating friendly competition and sharing best practices across teams.

**Key Metrics:** Team-by-team acceptance rates, suggestion counts, comparative analysis

**Target Audience:** Team leads, engineering managers, directors overseeing multiple teams

---

Panels:
1. Number of Teams (4)

Count of teams in the organization
Bar shows "octodemo-copilot-standalone"

2. Top Teams by Accepted Prompts - Pie Chart

All 4 teams equal (3 acceptances each)
se-field-admins, no-team, copilot-cli-team, asia-dev-gbb

3. Top Teams by Acceptance Rate - Pie Chart

All teams at 50% acceptance rate
Balanced usage across teams

4. Teams Breakdown - Table

Per-team metrics:
team_slug
Acceptances count
Suggestions count
Lines accepted
Lines suggested
Acceptance rate by count
Acceptance rate by lines

Row 4: Languages
**API Used:** Breakdown from copilot usage API (by language)

**Purpose:** Language-specific Copilot effectiveness analysis. Identifies which programming languages Copilot performs best/worst for in your codebase. Answers: "Where is Copilot most productive?" and "Which languages need model fine-tuning or training?" Critical for understanding technical ROI by language stack.

**Key Metrics:** Acceptance rates by language, suggestion counts, language distribution

**Target Audience:** Tech leads, architects, platform engineers, language-specific teams

---

Panels:
1. Number of Languages (3)

3 programming languages used
Yellow bar: octodemo-copilot-standalone


2. Top Languages by Accepted Prompts - Pie Chart

Python: 8 acceptances (66.7% - yellow)
scminput: 4 acceptances (green)
Java: 0 acceptances (blue)
3. Top Languages by Acceptance Rate - Pie Chart

Python: 66.7%
scminput: 50%
Java: 0%
4. Languages Breakdown - Table

Per-language detailed metrics
Same structure as Teams breakdown




Row 5: Editors
**API Used:** Breakdown from copilot usage API (by editor)

**Purpose:** IDE/Editor tooling analysis showing which development environments your team uses and how Copilot performs in each. Answers: "Should we standardize on one editor?" and "Where do we need editor-specific plugins or training?" Helps optimize tooling investments and support resources.

**Key Metrics:** Editor usage distribution, acceptance rates by editor, standardization metrics

**Target Audience:** DevOps, platform engineers, IT, developer experience teams

---

Panels:
1. Number of Editors (1)

Only VS Code in use
Yellow bar for octodemo-copilot-standalone
2. Top Editors by Accepted Prompts - Pie Chart

VS Code: 12 acceptances (100%)
All green circle
3. Top Editors by Acceptance Rate - Pie Chart

VS Code: 50%
4. Editors Breakdown - Table

Detailed VS Code metrics
12 acceptances / 24 suggestions = 50%



Row 6: Copilot Chat
**API Used:** Chat-specific data from copilot usage breakdown

**Purpose:** Conversational AI usage analysis tracking how developers use Copilot Chat for learning, debugging, and code generation. Answers: "Are developers leveraging Chat effectively?" and "Is chat driving code productivity?" Critical for understanding if users are exploring vs. implementing. Low acceptance with high turns = training opportunity.

**Key Metrics:** Chat turns (questions asked), chat acceptances (code inserted), active chat users, insert/copy events

**Target Audience:** Training teams, AI enablement, developer advocates, learning & development

---

Panels:
1. Acceptance Rate Average (0%)

Chat acceptances / chat turns
0% indicates no chat responses were inserted into code
2. Total Acceptances | Total Turns Count - Time Series

Blue line: Chat turns (interactions)
Peaks: 80 turns on 11/03, 20 on 11/25
Purple line: Acceptances (code insertions from chat)

Chat Turns = Number of questions asked (input)
Chat Acceptances = Number of times code from chat responses was inserted/copied (output action)


3. Total Active Copilot Chat Users - Bar Chart

4 active chat users on 11/03, 11/05, 11/24, 11/25
Shows chat adoption

4. No. of Insert / Cumulative (0 inserts)

Yellow: 0 code insertions from chat
5. No. of Copy / Cumulative (0 copies)

Purple: 0 code copies from chat responses




Row 7: Seat Analysis
**API Used:**
- GET /orgs/{org}/copilot/billing/seats
- GET /orgs/{org}/copilot/billing/seat_assignments

**Purpose:** License optimization and cost management dashboard. Identifies unused seats, inactive users, and engagement gaps. Answers: "Are we wasting money on unused licenses?" and "Which users should we onboard or offboard?" Critical for maximizing ROI and justifying seat expansion or consolidation.

**Key Metrics:** Total seats, never-active users, inactive users (>2 days), last activity dates, seat assignment details

**Target Audience:** Finance, procurement, IT asset management, program managers, budget owners

---

Panels:
1. Copilot Plan Type (12 business seats)

Shows seat allocation
2. Total Seats (0)

Seems inconsistent with business seats count
3. Assigned But Never Active (0)

Users assigned seats but never used Copilot
4. Never Active Users - List

Lists: vandana_octocps, son7211_octocps, shinyay_octocps, satomic_octocps, loganporelle_octocps
5. Ranking of Inactive Users (≥‰ × 2 days)

Horizontal bar chart showing inactivity:
devrajmehta_octocps: 49 days inactive (red)
umaranit_octocps: 19 days inactive (yellow)
neildcruz_octocps: 7 days inactive (green)
6. All Assigned Seats - Table

Comprehensive seat information:
assignee_login
day (last activity date: 2025-11-26)
assignee_team_slug
days_since_last_activity
is_active_today
last_activity_at
last_activity_editor
last_updated_at




Row 8: Breakdown Heatmap
**API Used:** Time-series breakdown data from `copilot_usage_breakdown` index

**Purpose:** Visual timeline analysis showing patterns of Copilot adoption across languages, editors, and time periods. Helps identify which languages/editors have strong adoption vs. those needing attention.

---

### Panel 1: Active Users Count (Group by Language) - Heatmap

**What It Shows:**
- Number of unique active Copilot users per day, grouped by programming language
- Time series visualization (X-axis = date, Y-axis = language)

**How to Read:**
- **Each row** = One programming language (Python, scminput, Java)
- **Each column** = One day in time range
- **Bar height** = Number of active users that day

**Color Coding:**
- **Green bars** = Active users present
- **No bar/empty** = Zero active users that day
- **Darker green** = More users active

**Your Data Example:**
- **Python**: Green bars on 11/02-11/04 and 11/25 (users were coding in Python)
- **scminput**: Active on specific dates
- **Java**: Minimal/no activity bars

**Business Insight:** Identifies which languages your team actively uses with Copilot. Gaps indicate languages where Copilot adoption is low.

---

### Panel 2: Active Users Count (Group by Editor) - Heatmap

**What It Shows:**
- Number of unique active Copilot users per day, grouped by code editor (VS Code, JetBrains, etc.)

**How to Read:**
- **Each row** = One code editor (vscode, intellij, vim, etc.)
- **Each column** = One day
- **Bar height** = Number of users active in that editor

**Color Coding:**
- **Green bars** = Users active in that editor
- **No bar** = No Copilot usage in that editor that day
- **Tooltip** = Shows exact timestamp and editor name (e.g., "2025-11-02 05:30:00, vscode")

**Your Data Example:**
- **VS Code**: Green bars on 11/02-11/04, 11/25 (all users using VS Code)
- Only one editor in use = standardized tooling (good for consistency)

**Business Insight:** Shows editor preferences across your team. Multiple editors may indicate need for editor-specific training. Single editor = easier to standardize support.

---

### Panel 3: Accept Rate by Count (%) - Heatmap

**What It Shows:**
- Acceptance rate percentage (suggestions accepted ÷ suggestions shown × 100) per day, grouped by language
- Measures **quality of suggestions** - higher % = Copilot is providing relevant code

**How to Read:**
- **Each row** = One programming language
- **Each column** = One day
- **Bar height + color** = Acceptance rate percentage for that language on that day

**Color Coding (Traffic Light System):**
- 🔴 **Red (0-30%)** = Low acceptance - Copilot struggling with this language
- 🟡 **Yellow/Orange (30-50%)** = Moderate acceptance - room for improvement
- 🟢 **Green (50-70%)** = Good acceptance - Copilot performing well
- 🔵 **Blue (70-100%)** = Excellent acceptance - highly relevant suggestions

**Your Data Example:**
- **Python**: Green bars on 11/04, 11/25 showing **66.7%** = Copilot provides high-quality Python suggestions
- **scminput**: Green bar on 11/25 showing **50%** = Moderate performance
- **Java**: Red bar on 11/04 showing **0%** = Zero suggestions accepted (major issue!)

**Business Insight:** 
- **Green languages** = Keep using Copilot, it's effective
- **Red languages** = Investigate why (bad suggestions? lack of training? wrong model?)
- **Java at 0%** = Critical problem - users not accepting suggestions at all

---

### Panel 4: Accept Rate by Lines (%) - Heatmap

**What It Shows:**
- Acceptance rate calculated by **lines of code** (LOC accepted ÷ LOC suggested × 100) instead of suggestion count
- Measures **volume impact** - how much code is actually being added

**How to Read:**
- **Each row** = One code editor (since grouped by editor)
- **Each column** = One day
- **Bar height + color** = Percentage of suggested lines that were accepted

**Color Coding (Same Traffic Light System):**
- 🔴 **Red (0-30%)** = Low line acceptance - users cherry-picking small portions
- 🟡 **Yellow/Orange (30-50%)** = Moderate - accepting about half
- 🟢 **Green (50-70%)** = Good - most suggested code is useful
- 🔵 **Blue (70-100%)** = Excellent - nearly all code suggestions accepted

**Your Data Example:**
- **VS Code**: Red bars on 11/04, 11/25 showing **50%** = Users accepting half of suggested lines
- Note: 50% is actually on the border between yellow and green (moderate to good)

**Difference from Panel 3:**
- **Panel 3** = Counts individual suggestions (accepted 2 out of 4 suggestions = 50%)
- **Panel 4** = Counts lines of code (accepted 100 lines out of 200 suggested = 50%)
- A user might accept 1 suggestion but only take 10 lines out of 50 suggested lines

**Business Insight:**
- **Panel 3 vs Panel 4 comparison** reveals if users are accepting whole suggestions or editing them heavily
- If Panel 3 is high but Panel 4 is low = users accept suggestions but heavily modify them
- If both are high = Copilot generating accurate, production-ready code

---

### How to Use These Heatmaps in Client Demo:

**1. Identify Patterns:**
- "Notice the green clusters on 11/03 and 11/24-11/26? This shows team activity bursts."
- "Gaps between dates indicate weekends or periods with no Copilot usage."

**2. Compare Languages:**
- "Python shows consistent green bars (66.7% acceptance) = Copilot excels here"
- "Java shows red bars (0% acceptance) = Training opportunity or model limitation"

**3. Time-Based Insights:**
- "Activity concentrated around specific sprints or deadlines"
- "Daily patterns reveal when developers most actively use Copilot"

**4. Action Items:**
- **Red bars** → Investigate: Are suggestions poor? Need training? Wrong context?
- **Green bars** → Success story: Share best practices from these users/languages
- **Empty spaces** → Engagement gap: Why no activity? Awareness? Onboarding?

**5. ROI Story:**
- "Green heatmap = productive days where Copilot accelerated development"
- "50%+ acceptance rates = Copilot saving significant development time"
- "Consistent patterns = Copilot integrated into daily workflow"




Key Insights for Client Demo
1. Adoption Health (Top 10 Panel)
1 user at 100% adoption (excellent!)
1 user at 24.2% adoption (needs improvement)
Action: Target training for lower adopters
2. Usage Patterns
Peak activity on 11/03 and 11/24-11/26
50% overall acceptance rate (industry average)
VS Code is primary editor (standardize tooling)
3. Seat Optimization
5 users never activated (reclaim seats)
Several users inactive 19-49 days (engagement opportunity)
ROI Impact: Optimize seat allocation
4. Language Trends
Python dominates (66.7% acceptance)
Java needs attention (0% acceptance)
Training: Language-specific enablement
5. Chat Adoption Gap
High chat usage (80 turns) but 0% code insertion
Users exploring but not implementing suggestions
Opportunity: Chat effectiveness training