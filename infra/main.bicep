targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

param updateGrafanaExists bool
@secure()
param updateGrafanaDefinition object

param cpuAdUpdaterExists bool
@secure()
param cpuAdUpdaterDefinition object

param elasticSearchExists bool
@secure()
param elasticSearchDefinition object

param grafanaExists bool
@secure()
param grafanaDefinition object

@description('Id of the user or app to assign application roles')
param principalId string

@secure()
param grafanaUsername string = ''

@secure()
param grafanaPassword string = ''

@secure()
@description('GitHub Personal Access Token (PAT) for authentication with permissions `manage_billing:copilot`, `read:enterprise`, `read:org`')
param githubPat string

@description('The Slugs of all Organizations that you want to monitor, which can be one or multiple separated by `,` (English symbol). **If you are using Copilot Standalone, use your Standalone Slug here, prefixed with `standalone:`, for example `standalone:YOUR_STANDALONE_SLUG`**. Please replace `<YOUR_ORGANIZATION_SLUGS>` with the actual value. For example, the following types of values are supported: `myOrg1`, `myOrg1,myOrg2`, `standalone:myStandaloneSlug`, `myOrg1,standalone:myStandaloneSlug`')
param githubOrganizationSlugs string

param elasticSearchImageName string = ''
param grafanaImageName string = ''

// Tags that should be applied to all resources.
// 
// Note that 'azd-service-name' tags should be applied separately to service host resources.
// Example usage:
//   tags: union(tags, { 'azd-service-name': <service name in azure.yaml> })
var tags = {
  'azd-env-name': environmentName
}

// Organize resources in a resource group
// resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
//   name: 'rg-${environmentName}'
//   location: location
//   tags: tags
// }

module resources 'resources.bicep' = {
  scope: resourceGroup()
  name: 'resources'
  params: {
    location: location
    tags: tags
    principalId: principalId
    updateGrafanaExists: updateGrafanaExists
    updateGrafanaDefinition: updateGrafanaDefinition
    cpuAdUpdaterExists: cpuAdUpdaterExists
    cpuAdUpdaterDefinition: cpuAdUpdaterDefinition
    elasticSearchExists: elasticSearchExists
    elasticSearchDefinition: elasticSearchDefinition
    elasticSearchImageName: elasticSearchImageName
    grafanaExists: grafanaExists
    grafanaDefinition: grafanaDefinition
    grafanaImageName: grafanaImageName
    grafanaPassword: grafanaPassword
    grafanaUsername: grafanaUsername
    githubPat: githubPat
    githubOrganizationSlugs: githubOrganizationSlugs
  }
}

output AZURE_RESOURCE_UPDATE_GRAFANA_ID string = resources.outputs.AZURE_RESOURCE_UPDATE_GRAFANA_ID
output AZURE_RESOURCE_UPDATE_GRAFANA_NAME string = resources.outputs.AZURE_RESOURCE_UPDATE_GRAFANA_NAME
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.AZURE_CONTAINER_REGISTRY_LOGIN_SERVER
output AZURE_CONTAINER_REGISTRY_NAME string = resources.outputs.AZURE_CONTAINER_REGISTRY_NAME
output AZURE_RESOURCE_CPUAD_UPDATER_ID string = resources.outputs.AZURE_RESOURCE_CPUAD_UPDATER_ID
output AZURE_RESOURCE_CPUAD_UPDATER_NAME string = resources.outputs.AZURE_RESOURCE_CPUAD_UPDATER_NAME
output AZURE_RESOURCE_ELASTIC_SEARCH_ID string = resources.outputs.AZURE_RESOURCE_ELASTIC_SEARCH_ID
output AZURE_RESOURCE_GRAFANA_ID string = resources.outputs.AZURE_RESOURCE_GRAFANA_ID
output AZURE_RESOURCE_GROUP_NAME string = resourceGroup().name
output AZURE_CONTAINER_APPS_ENVIRONMENT_NAME string = resources.outputs.AZURE_CONTAINER_APPS_ENVIRONMENT_NAME
output AZD_IS_PROVISIONED bool = true
output SERVICE_UPDATEGRAFANA_RESOURCE_EXISTS bool = resources.outputs.SERVICE_UPDATEGRAFANA_RESOURCE_EXISTS
output SERVICE_CPUADUPDATER_RESOURCE_EXISTS bool = resources.outputs.SERVICE_CPUADUPDATER_RESOURCE_EXISTS
