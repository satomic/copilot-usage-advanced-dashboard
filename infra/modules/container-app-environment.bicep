param location string
param abbrs object
param resourceToken string
param logAnalyticsWorkspaceResourceId string
param storages array
param publicNetworkAccess string
param workloadProfileType string
param infrastructureSubnetId string
param appInsightsConnectionString string

var workloadProfileName = 'default'

// Container apps environment
module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.10.0' = {
  name: 'container-apps-environment'
  params: {
    logAnalyticsWorkspaceResourceId: logAnalyticsWorkspaceResourceId
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    zoneRedundant: false
    storages: storages
    publicNetworkAccess: publicNetworkAccess
    infrastructureSubnetId: infrastructureSubnetId
    workloadProfiles: [
      {
        name: workloadProfileName
        workloadProfileType: workloadProfileType
        minimumCount: 1
        maximumCount: 10
      }
    ]
    appInsightsConnectionString: appInsightsConnectionString
    openTelemetryConfiguration:{
      tracesConfiguration: {
        destinations: ['appInsights']
      }
      logsConfiguration: {
        destinations: ['appInsights']
      }
    }
  }
}

output AZURE_RESOURCE_CONTAINER_APPS_ENVIRONMENT_ID string = containerAppsEnvironment.outputs.resourceId
output AZURE_RESOURCE_CONTAINER_APPS_WORKLOAD_PROFILE_NAME string = workloadProfileName
output AZURE_RESOURCE_CONTAINER_APPS_WORKLOAD_PROFILE_CONSUMPTION string = 'Consumption'
output AZURE_RESOURCE_CONTAINER_APPS_ENVIRONMENT_NAME string = containerAppsEnvironment.outputs.name
