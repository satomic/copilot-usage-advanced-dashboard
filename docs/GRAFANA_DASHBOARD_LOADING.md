# Grafana Dashboard Loading Reference

## How Dashboards Are Loaded into Grafana

### Primary File
**File**: `src/cpuad-updater/grafana/dashboard-template.json`

This is the **source template** for the Grafana dashboard. Any changes to the dashboard configuration should be made here.

### Loading Process

1. **Script**: `src/cpuad-updater/grafana/update_grafana.py`
   - Reads `dashboard-template.json`
   - Replaces datasource UID placeholders with actual UIDs from Grafana API
   - Imports the dashboard via Grafana API

2. **Container**: `init-grafana` (defined in `docker-compose.yml`)
   - Runs `update_grafana.py` on startup
   - Provisions datasources and imports dashboard automatically

### Manual Dashboard Re-import

To reload the dashboard after making changes to the template:

```powershell
# Rebuild and run the init-grafana container
docker compose build init-grafana
docker compose run --rm init-grafana python /app/update_grafana.py
```

### Environment Variables Required

The `init-grafana` service needs these environment variables (set in `docker-compose.yml`):
- `GRAFANA_URL`: http://grafana:80
- `GRAFANA_USERNAME`: admin
- `GRAFANA_PASSWORD`: Copilot2024 (updated from default)
- `ELASTICSEARCH_URL`: http://elasticsearch:9200

### Key Configuration Details

#### Top 10 Copilot Users Panel
- **Datasource**: `elasticsearch-user-adoption` (UID: `ff57sd6383egwa`)
- **Index**: `copilot_user_adoption`
- **Time Field**: `@timestamp`
- **Aggregation Field**: `user_login` (NOT `user_login.keyword` - field is already keyword type)
- **Metric**: `max(adoption_pct)`

### Important Notes

1. The `user_login` field in `copilot_user_adoption` index is mapped directly as `keyword` type, not as `text` with `.keyword` subfield
2. Grafana admin password was changed from default `copilot` to `Copilot2024` - docker-compose.yml reflects this
3. Dashboard template uses hardcoded UID `ff57sd6383egwa` for user-adoption datasource instead of placeholder

### Files Modified in Fix
- `src/cpuad-updater/grafana/dashboard-template.json`: Fixed datasource UID and field name
- `docker-compose.yml`: Updated Grafana password for init-grafana service
