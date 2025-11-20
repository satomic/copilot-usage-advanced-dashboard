# Learning Environment Configuration

This file contains configuration for your personal learning environment.
DO NOT commit this to the main branch - keep it in your feature branch only.

## Your Personal Environment Settings

### Elasticsearch (Your Learning Instance)
```bash
# Replace with your Elastic Cloud details
ELASTICSEARCH_URL=https://your-cluster.es.us-central1.gcp.cloud.es.io:9243
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASS=your-generated-password

# Your GitHub Settings
# Set your GitHub PAT
$env:GITHUB_PAT="your_github_pat_here"
ORGANIZATION_SLUGS=your-test-org  # Use a test org for learning

# Your Grafana Settings  
GRAFANA_URL=https://your-org.grafana.net
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=your-password
```

### Index Names (Keep them separate from demo)
```bash
INDEX_SEAT_INFO=learning_copilot_seat_info_settings
INDEX_SEAT_ASSIGNMENTS=learning_copilot_seat_assignments  
INDEX_NAME_TOTAL=learning_copilot_usage_total
INDEX_NAME_BREAKDOWN=learning_copilot_usage_breakdown
INDEX_NAME_BREAKDOWN_CHAT=learning_copilot_usage_breakdown_chat
INDEX_USER_METRICS=learning_copilot_user_metrics
INDEX_USER_ADOPTION=learning_copilot_user_adoption
```

## How This Keeps You Safe

1. **Different Index Names** - Your data won't interfere with demo
2. **Different Clusters** - Completely separate infrastructure  
3. **Feature Branch** - Your changes won't affect main demo
4. **Environment Variables** - Easy to switch between environments

## When Ready to Integrate

Later, you can simply:
1. Change the environment variables to point to production
2. Update index names to match production naming
3. Test everything works
4. Submit PR to original repo

## Cost Estimate

- **Elastic Cloud Free Tier**: $0 for learning
- **Grafana Cloud Free**: $0 for learning  
- **GitHub API**: Free (rate limited)
- **Total Learning Cost**: $0

## Next Steps

1. Sign up for Elastic Cloud
2. Sign up for Grafana Cloud  
3. Update this config with your credentials
4. Test the connection
5. Start developing!