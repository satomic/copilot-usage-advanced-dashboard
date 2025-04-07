param location string
param tags object
param name string
param definition object
param fetchLatestImage object
param applicationInsightsConnectionString string
param userAssignedManagedIdentityClientId string
param userAssignedManagedIdentityResourceId string
param containerRegistryLoginServer string
param containerAppsEnvironmentResourceId string
param cpu string
param memory string
param volumeMounts array = []
param volumes array = []
param workloadProfileName string
param cronExpression string = ''
param triggerType string

import {secretType} from 'br/public:avm/res/app/job:0.6.0'

var appSettingsArray = filter(array(definition.settings), i => i.name != '')
var secrets = map(filter(appSettingsArray, i => i.?secret != null), i => {
  name: i.name
  value: i.value
  secretRef: i.?secretRef ?? take(replace(replace(toLower(i.name), '_', '-'), '.', '-'), 32)
})
var srcEnv = map(filter(appSettingsArray, i => i.?secret == null), i => {
  name: i.name
  value: i.value
})

module job 'br/public:avm/res/app/job:0.6.0' = {
  name: 'containerJobDeployment-${name}'
  params: {
    name: name
    triggerType: triggerType
    manualTriggerConfig: triggerType == 'Manual' ? {
      parallelism: 1
      replicaCompletionCount: 1
    } : null
    scheduleTriggerConfig: triggerType == 'Schedule' ?{
      cronExpression: cronExpression
    } : null
    workloadProfileName: workloadProfileName
    secrets: union([],
      map(secrets, secret => {
        name: secret.secretRef
        value: secret.value
      }))
    
    containers: [
      {
        image: fetchLatestImage.outputs.?containers.?value[?0].?image ?? 'mcr.microsoft.com/k8se/quickstart-jobs:latest'
        name: 'main'
        resources: {
          cpu: cpu
          memory: memory
        }
        volumeMounts: volumeMounts
        env: union([
          {
            name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
            value: applicationInsightsConnectionString
          }
          {
            name: 'AZURE_CLIENT_ID'
            value: userAssignedManagedIdentityClientId
          }
        ],
        srcEnv,
        map(secrets, secret => {
            name: secret.name
            secretRef: secret.secretRef
        }))
      }
    ]
    managedIdentities:{
      systemAssigned: false
      userAssignedResourceIds: [userAssignedManagedIdentityResourceId]
    }
    registries:[
      {
        server: containerRegistryLoginServer
        identity: userAssignedManagedIdentityResourceId
      }
    ]
    environmentResourceId: containerAppsEnvironmentResourceId
    location: location
    tags: union(tags, { 'azd-service-name': name })
    volumes: volumes
  }
}

output outputs object = fetchLatestImage.outputs
output containers object = fetchLatestImage.outputs.?containers
output index_zero object = fetchLatestImage.outputs.?containers.?value[?0]
output image string = fetchLatestImage.outputs.?containers.?value[?0].?image
output AZURE_RESOURCE_CONTAINER_APP_ID string = job.outputs.resourceId
output AZURE_RESOURCE_CONTAINER_APP_NAME string = job.outputs.name
