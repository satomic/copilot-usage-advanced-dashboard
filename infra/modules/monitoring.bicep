param location string
param tags object
param abbrs object
param resourceToken string

// Monitor application with Azure Monitor
module monitoring 'br/public:avm/ptn/azd/monitoring:0.1.0' = {
  name: 'monitoring'
  params: {
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
    applicationInsightsDashboardName: '${abbrs.portalDashboards}${resourceToken}'
    location: location
    tags: tags
  }
}

output AZURE_RESOURCE_MONITORING_LOG_ANALYTICS_ID string = monitoring.outputs.logAnalyticsWorkspaceResourceId
output AZURE_RESOURCE_MONITORING_APP_INSIGHTS_ID string = monitoring.outputs.applicationInsightsResourceId
output AZURE_RESOURCE_MONITORING_APP_INSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString
output AZURE_RESOURCE_MONITORING_APP_INSIGHTS_NAME string = monitoring.outputs.applicationInsightsName
output AZURE_RESOURCE_MONITORING_LOG_ANALYTICS_WORKSPACE_NAME string = monitoring.outputs.logAnalyticsWorkspaceName
