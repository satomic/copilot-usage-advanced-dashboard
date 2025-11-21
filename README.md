# Copilot Usage Advanced Dashboard Tutorial


> ⚠️**Disclaimer**: This project is open sourced to solve problems that are critical to some users, and the functions provided may not be natively provided by GitHub Copilot. Therefore the contents,  opinions and views expressed in this project are solely mine do not necessarly refect the views of my employer, These are my personal notes based on myunderstanding of the code and trial deployments to GitHub Copilot. If anything is wrong with this article, please let me know through the [issues](https://github.com/satomic/copilot-usage-advanced-dashboard/issues/new). l appreciate your help in correcting my understanding.

> ✅**Risk Warning**: This project uses the standard Copilot REST API to obtain data, aggregate data, and visualize it, without any potential risks.


[Copilot Usage Advanced Dashboard 教程](https://www.wolai.com/tNxKtCqCfb6DR2cuaxmJDZ)

|**Version**|**Update Notes**|**Date**|
|-|-|-|
|1.0 |Document creation |20241217|
|1.1|Some updates|20241218|
|1.1|Add new templates|20241221|
|1.2|Support Copilot Standalone, thanks [sombaner](https://github.com/sombaner)'s great feedback |20241224|
|1.3|Compatible with metrics API|20250208|
|1.4|1. [Distinguish between insert and copy events of chat](https://github.com/satomic/copilot-usage-advanced-dashboard/issues/8)<br>2. [Add model filter variables](https://github.com/satomic/copilot-usage-advanced-dashboard/issues/6)<br>3. [Compatible with organizations that do not have teams](https://github.com/satomic/copilot-usage-advanced-dashboard/issues/9)<br>4. Fixed some bugs, for upgrades to older versions before `20250220`, please refer to [Old version (`<=20250220`) upgrade steps](https://github.com/satomic/copilot-usage-advanced-dashboard/issues/10)|20250222|
|1.5| Add daily usage history for each user, old version upgrade guide refer to [this issue](https://github.com/satomic/copilot-usage-advanced-dashboard/issues/10)  | 20250404 |
|1.6| refactor timezone handling in main.py & Docker run ENV paras |20250410|
|1.7| [Add Elasticsearch authentication](https://github.com/satomic/copilot-usage-advanced-dashboard/pull/19) |20250411|
|1.8| **User Metrics Analytics Module**: Added 5th data source with user adoption leaderboard, Top 10 visualization, hourly automation, and production-ready deployment |20251120|

## Table of contents

- [🚀 Quick Start](#-quick-start-5-minutes)
- [Introduction](#Introduction)
  - [Online Demo Environment ✨](#Online-Demo-Environment)
    - [Copilot Usage Advanced Dashboard](#Copilot-Usage-Advanced-Dashboard)
    - [Copilot Usage Advanced Dashboard Original](#Copilot-Usage-Advanced-Dashboard-Original)
- [Variables](#Variables)
- [Features](#Features)
  - [Copilot Usage Advanced Dashboard](#Copilot-Usage-Advanced-Dashboard)
    - [1. Organization](#1-Organization)
    - [2. Teams](#2-Teams)
    - [3. Languages](#3-Languages)
    - [4. Editors](#4-Editors)
    - [5. Copilot Chat](#5-Copilot-Chat)
    - [6. Seat Analysis](#6-Seat-Analysis)
    - [7. Breakdown Heatmap](#7-Breakdown-Heatmap)
    - [8. User Metrics Analytics](#8-User-Metrics-Analytics)
  - [Copilot Usage Advanced Dashboard Original](#Copilot-Usage-Advanced-Dashboard-Original)
    - [1. Copilot Seat Info & Top Languages](#1-Copilot-Seat-Info--Top-Languages)
    - [2. Copilot Usage Total Insight](#2-Copilot-Usage-Total-Insight)
    - [3. Copilot Usage Breakdown Insight](#3-Copilot-Usage-Breakdown-Insight)
- [Deployment](#deployment)
  - [1. Azure Container Apps](#1-Azure-Container-Apps)
  - [2. Linux with Docker](#2-Linux-with-Docker)
  - [3. Kubernetes](#3-Kubernetes)
- [Congratulations](#Congratulations)

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- GitHub Personal Access Token with `manage_billing:copilot` scope ([Create Token](https://github.com/settings/tokens))
- Your GitHub Organization/Enterprise slug

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/vanchaudhary/copilot-usage-advanced-dashboard.git
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

# Introduction

[Copilot Usage Advanced Dashboard](https://github.com/satomic/copilot-usage-advanced-dashboard) is a single data panel display that almost fully utilizes data from Copilot APIs, The APIs used are:

- [List teams of an organization](https://docs.github.com/en/enterprise-cloud@latest/rest/teams/teams?apiVersion=2022-11-28#list-teams)
- [Get a summary of Copilot metrics for a team](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-metrics?apiVersion=2022-11-28#get-copilot-metrics-for-a-team)
- [Get Copilot seat information and settings for an organization](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-user-management?apiVersion=2022-11-28#get-copilot-seat-information-and-settings-for-an-organization)
- [List all Copilot seat assignments for an organization](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-user-management?apiVersion=2022-11-28#list-all-copilot-seat-assignments-for-an-organization)
- [**NEW in v1.8** - Get Copilot User Metrics (28-day rolling window)](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-user-metrics)

representing Copilot usage in multi organizations & teams from different dimensions. The features are summarized as follows:
- Data is persisted in Elasticsearch and visualized in Grafana, **not just the past 28 days**. So you can freely choose the time period you want to visualize, such as the past year or a specific month.
- You can freely adjust the style and theme of the chart, everything is a mature feature of Grafana.
- All stored data includes Organization and Team fields, which is convenient for data filtering through variable filters.
- Generate a unique hash key for each piece of data, and update the stored data every time the latest data is obtained.
- Visualizations in Grafana dashboards can be adjusted or deleted according to actual needs.
- Based on Grafana's built-in alerting function, you can set alert rules for some inappropriate usage behaviors, such as sending alerts to users who have been inactive for a long time.
- It can be easily integrated with third-party systems, whether it is extracting data from Elasticsearch to other data visualization platforms for data visualization, or adding other data sources in the Copilot Usage Advanced Dashboard for joint data visualization.

## Online Demo Environment

> Designed 2 dashboards, both can exist at the same time in Grafana.

![](image/image_m8r5-tO_h-.png)

### Copilot Usage Advanced Dashboard

> Copilot Metrics Viewer compatible dashboard

> If you are familiar with the [copilot-metrics-viewer](https://github.com/github-copilot-resources/copilot-metrics-viewer) project, then please try this dashboard and use it in subsequent deployments.

- link: [copilot-usage-advanced-dashboard](https://softrin.com/d/be7hpbvvhst8gc/copilot-usage-advanced-dashboard)
- username：`demouser`
- password：`demouser`

  ![](image/image_KGwt1NLyRT.png)

### Copilot Usage Advanced Dashboard Original

> New designed dashboard&#x20;

- Link: [copilot-usage-advanced-dashboard-original](https://softrin.com/d/a98455d6-b401-4a53-80ad-7af9f97be6f4/copilot-usage-advanced-dashboard-original)
- username：`demouser`
- password：`demouser`

  ![](image/cpuad_full_FkIGG_4fzg.png)

# Variables

Supports four filtering varibales, namely

- Organzation
- Team
- Language
- Editor

The choice of variables is dynamically associated with the data display

![](image/image_filters.png)

# Features

## Copilot Usage Advanced Dashboard

### 1. Organization
> First, based on [List teams of an onganization](https://docs.github.com/en/enterprise-cloud@latest/rest/teams/teams?apiVersion=2022-11-28#list-teams), get all the teams under the Organization, and then based on [Get a summary of Copilot usage for a team](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-a-team), sum and calculate the data of all teams under the Organization to get complete Organization-level data.

- Acceptance Rate Average = `sum(total_acceptances_count) / sum(total_suggestions_count)`
- Cumulative Number of Acceptence (Count) = `sum(total_acceptances_count)`
- Cumulative Number of Suggestions (Count) = `sum(total_suggestions_count)`
- Cumulative Number of Lines of Code Accepted = `sum(total_lines_accepted)`
- Acceptance Rate (%) = `total_acceptances_count / total_suggestions_count`
- Total Active Users = `total_active_users`
- Total Suggestions & Acceptances Count = `total_suggestions_count` & `total_acceptances_count`
- Total Lines Suggested & Accepted = `total_lines_suggested `& `total_lines_accepted`

![](image/image_WVNHVnb2OZ.png)

### 2. Teams
> Based on the breakdown data in [Get a summary of Copilot usage for a team](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-a-team), the data is aggregated by Teams to obtain data comparisons of different Teams.

- Number of Teams = `unique_count(team_slug)`
- Top Teams by Accepted Prompts = `sum(acceptances_count).groupby(team_slug)`
- Top Teams by Acceptance Rate = `sum(acceptances_count).groupby(team_slug) / sum(suggestions_count).groupby(team_slug)`
- Team Breakdown = `sum(*).groupby(team_slug)`

![](image/image_TGcs3tD7Cs.png)

### 3. Languages

> Based on the breakdown data in [Get a summary of Copilot usage for a team](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-a-team), the data is aggregated according to Languages ​​to obtain data comparisons for different Languages.

- Number of Languages= `unique_count(language)`
- Top Languages by Accepted Prompts = `sum(acceptances_count).groupby(language)`
- Top Languages by Acceptance Rate = `sum(acceptances_count).groupby(language) / sum(suggestions_count).groupby(language)`
- Languages Breakdown = `sum(*).groupby(language)`

![](image/image_YHXpu1wRf2.png)

### 4. Editors

> Based on the breakdown data in [Get a summary of Copilot usage for a team](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-a-team), the data is aggregated by Editors to obtain data comparisons for different Editors.

- Number of Editors = `unique_count(editor)`
- Top Editors by Accepted Prompts = `sum(acceptances_count).groupby(editor)`
- Top Editors by Acceptance Rate = `sum(acceptances_count).groupby(editor) / sum(suggestions_count).groupby(editor)`
- Editors Breakdown = `sum(*).groupby(editor)`

![](image/image_9P1zJxBMaO.png)

### 5. Copilot Chat

> Based on the data from [Get a summary of Copilot usage for a team](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-a-team), we can get the usage of Copilot Chat.

- Acceptance Rate Average = `sum(total_chat_acceptances) / sum(total_chat_turns)`
- Cumulative Number of Acceptances = `sum(total_chat_acceptances)`
- Cumulative Number of Turns = `sum(total_chat_turns)`
- Total Acceptances | Total Turns Count = `total_chat_acceptances` | `total_chat_turns`
- Total Active Copilot Chat Users = `total_active_chat_users`

![](image/image_chat.png)

### 6. Seat Analysis

> Based on the data analysis of [Get Copilot seat information and settings for an organization](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-user-management?apiVersion=2022-11-28#get-copilot-seat-information-and-settings-for-an-organization) and [List all Copilot seat assignments for an organization](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-user-management?apiVersion=2022-11-28#list-all-copilot-seat-assignments-for-an-organization), the seat allocation and usage are presented in a unified manner.

- Copilot Plan Type = `count(seats).groupby(plan_type)`
- Total = `seat_breakdown.total`
- Active in this Cycle = `seat_breakdown.active_this_cycle`
- Assigned But Never Used = `last_activity_at.isnan()`
- Inactive in this Cycle = `seat_breakdown.inactive_this_cycle`
- Ranking of Inactive Users ( ≥ 2 days ) =  `today - last_activity_at`
- All assigned seats = `*`

![](image/image_vNpkYpc-xW.png)

### 7. Breakdown Heatmap

> Based on the breakdown data in [Get a summary of Copilot usage for a team](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-a-team), we analyze the data from two dimensions: Languages ​​and Editors. We can clearly see what combination of Languages ​​and Editors can achieve the best Copilot usage effect.

- Active Users Count (Group by Language) = `active_users.groupby(language)`
- Accept Rate by Count (%) = `sum(acceptances_count).groupby(language) / sum(suggestions_count).groupby(language)`
- Accept Rate by Lines (%) = `sum(lines_accepted).groupby(language) / sum(lines_suggested).groupby(language)`
- Active Users Count (Group by Editor) = `active_users.groupby(editor)`
- Accept Rate by Count (%) = `sum(acceptances_count).groupby(editor) / sum(suggestions_count).groupby(editor)`
- Accept Rate by Lines (%) = `sum(lines_accepted).groupby(editor) / sum(lines_suggested).groupby(editor)`

![](image/image_i7-wXGj-UA.png)

### 8. User Metrics Analytics

> **NEW in v1.8**: Complete user-level analytics powered by GitHub Copilot User Metrics API. Track individual user adoption, engagement patterns, and feature utilization with automated hourly updates.

Based on the data from [Get Copilot User Metrics](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-user-metrics), this module provides comprehensive per-user analytics including:

**Key Metrics:**
- **Total Users** = `cardinality(user_login)` - Unique users with Copilot activity
- **Total Suggestions** = `sum(code_generation_activity_count)` - Code suggestions generated across all users
- **Total Acceptances** = `sum(code_acceptance_activity_count)` - Code suggestions accepted by users
- **Acceptance Rate** = `sum(code_acceptance_activity_count) / sum(code_generation_activity_count)` - Overall acceptance percentage
- **Active Days** = `cardinality(day)` - Distinct days each user engaged with Copilot
- **Adoption Score** = `(active_days / total_days_in_period) × 100` - User engagement percentage

**Per-User Analytics Table:**
- User-initiated Interactions = `sum(user_initiated_interaction_count)`
- Code Suggestions Generated = `sum(code_generation_activity_count)`
- Code Suggestions Accepted = `sum(code_acceptance_activity_count)`
- Average LOC Suggested = `avg(loc_suggested_to_add_sum)`
- Average LOC Added = `avg(loc_added_sum)`
- Agent Usage = `sum(used_agent)` - Copilot Agent feature usage count
- Chat Usage = `sum(used_chat)` - Copilot Chat feature usage count
- Active Days = `cardinality(day)` - Days with any Copilot activity

**Top 10 Copilot Users Leaderboard:**
- Visualizes top 10 users by adoption percentage
- Color-coded gradient from red (low adoption) to blue (high adoption)
  - 🔴 Red (0-40%): Needs attention
  - 🟠 Orange (40-60%): Moderate usage
  - 🟡 Yellow (60-80%): Good engagement
  - 🟢 Green (80-95%): Excellent adoption
  - 🔵 Blue (95-100%): Power user

**Automated Data Collection:**
- Runs every hour (configurable via `EXECUTION_INTERVAL_HOURS`)
- Fetches 28-day rolling window data from GitHub API
- Calculates adoption scores automatically
- Stores in 2 Elasticsearch indexes: `copilot_user_metrics` (raw data) and `copilot_user_adoption` (leaderboard scores)
- No manual intervention required

![](image/user-metrics-dashboard.png)

**Use Cases:**
- Identify power users and champions for Copilot evangelism
- Track onboarding progress for new Copilot users
- Spot users who need additional training or support
- Measure team-level adoption trends over time
- Monitor Chat and Agent feature adoption rates
- Correlate active days with productivity metrics



### 1. Copilot Seat Info & Top Languages

- You can view the distribution of seats, Enterprise or Business? and overall activation trends. And for users who don't use Copilot, they are ranked based on the length of inactivity and list users who have never activated.
- Ranking Language and Teams based on usage

![](image/image_raciReXvQY.png)

### 2. Copilot Usage Total Insight

You can analyze the total number of recommendations and adoption rate trends based on Count Lines and Chats

![](image/image_6lcv61qm2_.png)

### 3. Copilot Usage Breakdown Insight

You can analyze the effect of Copilot in different languages ​​and different editor combinations.

![](image/image_RJ6lvMkZlP.png)

***



# Deployment

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

## Azure DevOps
If you are using Azure DevOps, make sure you change the name of the service connection to the name of your service connection.  You will need to change line
30 and 45 of the `azure-dev.yml` file located in the `.azdo/pipelines` folder.

To create a service connection you can use the azd pipeline config --provider azdo command from the terminal.  You can read more here:
https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/pipeline-azure-pipelines.

You will need to install the "Install azd" extension from the [marketplace](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.azd) in your Azure DevOps organization if you haven't already done so.

You will need to manually create the DevOps variables yourself in the Azure DevOps GUI.

## GitHub Actions
You will create a pipeline using the `azure-dev.yml` file located in the `.github/workflows` folder. You will need to manually create the GitHub variables yourself in the GitHub GUI.

## 1. Azure Container Apps
if you are using Azure Container Apps, please refer to the [Azure Container Apps deployment document](deploy/azure-container-apps.md).

![](image/architecture.drawio.png)

### Deploying as `Contributor`

Deployment adds required role assignments, which require `User Access Administrator` RBAC role (more permissions than `Contributor`) or `Owner` RBAC role.

To deploy as `Contributor` RBAC role, pass `doRoleAssignments` parameter set to `false` or set `AZURE_ROLE_ASSIGNMENTS` environment variable when deploying with `azd`.

Required role assignments:

- **Key Vault Secrets Officer** on the KeyVault assigned to User Assigned Identity
- **AcrPull** on the Azure Container Registry assigned to User Assigned Identity
- **Storage File Data SMB Share Contributor** on the Storage Account assigned to User Assigned Identity

## 2. Linux with Docker
If you are not using Azure, you can use Linux with Docker, please refer to the [Linux with Docker deployment document](deploy/linux-with-docker.md).

![](image/image_oZJ-KGOxa5.png)

## 3. Kubernetes
For cloud native deployment on Kubernetes,  please refer to the [Kubernetes deployment document](deploy/kubernetes.md).

---

# Congratulations

At this point, return to the Grafana page and refresh. You should be able to see the data.

![](image/image_lf08iyNeUt.png)

or

![](image/image_wjdhYnlwOZ.png)
