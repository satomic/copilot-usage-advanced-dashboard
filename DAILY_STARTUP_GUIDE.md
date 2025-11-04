# 🚀 Daily Application Startup Guide

## Quick Start Commands (Tomorrow & Every Day)

### 1. **Start the Application** 
```powershell
# Navigate to your project directory
cd C:\Users\vanchaudhary\copilot-usage-advanced-dashboard

# Set your GitHub PAT (if not already set in your session)
$env:GITHUB_PAT="your_github_pat_here"

# Start all services
docker-compose up --build -d
```

### 2. **Verify Services are Running**
```powershell
# Check all containers are up
docker-compose ps

# Should show:
# - elasticsearch (port 9200)
# - grafana (port 8080) 
# - cpuad-updater (processing data)
# - init-grafana (configures dashboards)
```

### 3. **Access Your Dashboard**
- **URL**: http://localhost:8080
- **Username**: admin
- **Password**: copilot

## 📊 **Verifying New User Metrics Features**

### **Step 1: Check Data is Loading**
```powershell
# Check Elasticsearch has user metrics data
Invoke-RestMethod -Uri "http://localhost:9200/copilot_user_metrics/_count" -Method GET

# Should return something like: {"count":4,"_shards":{...}}
```

### **Step 2: Import the Unified Dashboard**
1. Go to http://localhost:8080
2. Click **"+"** → **"Import"**
3. Upload: `src/cpuad-updater/grafana/copilot-unified-dashboard-structured.json`
4. Click **"Load"** → **"Import"**

### **Step 3: Verify User Metrics Analytics Row**
In your dashboard, you should see **8 collapsible rows**:
1. Organization ✅ 
2. Teams ✅
3. Languages ✅
4. Editors ✅
5. Copilot Chat ✅
6. Seat Analysis ✅
7. Breakdown Heatmap ✅
8. **User Metrics Analytics** ⭐ **NEW - Click to expand!**

### **Step 4: Check the 5 User Metrics Panels**
Click on **"User Metrics Analytics"** row to expand and verify:
- ✅ **Agent Usage Distribution** (Pie Chart)
- ✅ **User Activity Over Time** (Bar Chart)
- ✅ **Chat Usage Distribution** (Pie Chart) 
- ✅ **User Activity Over Time (Alternative)** (Line Chart)
- ✅ **User Activity Summary Table** (Detailed table)

## 🔍 **Troubleshooting Commands**

### **If No Data Shows:**
```powershell
# Check if data updater is running
docker logs cpuad-updater --tail 20

# Manually trigger data update
docker-compose restart cpuad-updater

# Check Elasticsearch indices
Invoke-RestMethod -Uri "http://localhost:9200/_cat/indices?v" -Method GET
```

### **If Dashboard Import Fails:**
```powershell
# Check Grafana logs
docker logs grafana --tail 20

# Restart Grafana
docker-compose restart grafana
```

### **If Services Won't Start:**
```powershell
# Stop everything and start fresh
docker-compose down
docker-compose up --build -d

# Check for port conflicts
netstat -an | findstr "9200\|8080"
```

## ⚡ **Quick Health Check (30 seconds)**
```powershell
# 1. Services status
docker-compose ps

# 2. Elasticsearch health  
curl http://localhost:9200/_cluster/health

# 3. Data count
curl http://localhost:9200/copilot_user_metrics/_count

# 4. Grafana access
curl http://localhost:8080/api/health
```

## 📈 **Expected Results**
- **Elasticsearch**: 5 indices with data (including copilot_user_metrics)
- **Grafana**: Dashboard with 8 rows, last one being "User Metrics Analytics"
- **Data**: Live GitHub Copilot usage data from your organization
- **Updates**: Data refreshes automatically every time you restart cpuad-updater

## 🎯 **Success Indicators**
✅ All Docker containers running  
✅ Grafana accessible at localhost:8080  
✅ User Metrics Analytics row visible in dashboard  
✅ 5 user metrics panels showing data  
✅ Data updates when you restart cpuad-updater  

---
**💡 Pro Tip**: Bookmark http://localhost:8080 and keep this guide handy for daily use!