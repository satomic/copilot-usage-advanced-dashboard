param location string
param tags object
param name string
param definition object
param existingImage string = ''
param applicationInsightsConnectionString string
param userAssignedManagedIdentityClientId string
param userAssignedManagedIdentityResourceId string
param ingressTargetPort int
param containerRegistryLoginServer string
param containerAppsEnvironmentResourceId string
param ingressExternal bool = false
param cpu string
param memory string
param volumeMounts array = []
param volumes array = []
param workloadProfileName string
param scaleMinReplicas int = 1
param scaleMaxReplicas int = 2
param probes array = []
param keyVaultName string // New parameter for Key Vault name
@description('Optional. List of specialized containers that run before app containers.')
param initContainersTemplate array = []
param authentication object = {}
param managedIdentityClientIdSecretName string = ''

var appSettingsArray = filter(array(definition.settings), i => i.name != '')
var secrets = map(filter(appSettingsArray, i => i.?secret != null), i => {
  name: i.name
  secretName: i.?keyVaultSecretName != null ? i.keyVaultSecretName : '' // Use Key Vault secret name
  secretUri: i.?keyVaultSecretName != null
    ? 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/${i.keyVaultSecretName}'
    : '' // Use Key Vault secret reference
  path: i.?path
})
var srcEnv = map(filter(appSettingsArray, i => i.?secret == null), i => {
  name: i.name
  value: i.value
})
var additionalVolumeMounts = union(
  length(secrets) > 0
    ? [
        {
          volumeName: 'secrets'
          mountPath: '/run/secrets'
        }
      ]
    : [],
  volumeMounts
)

var secretVolumePaths = map(filter(secrets, i => i.secretUri != null && i.path != null), i => {
  secretRef: i.secretName
  path: i.path
})

var additionalVolumes = union(
  length(secrets) > 0
    ? [
        {
          name: 'secrets'
          storageType: 'Secret'
          secrets: length(secretVolumePaths) > 0 ? secretVolumePaths : null
        }
      ]
    : [],
  volumes
)

module containerApp 'br/public:avm/res/app/container-app:0.17.0' = {
  name: 'containerAppDeployment-${name}'
  params: {
    name: name
    workloadProfileName: workloadProfileName
    ingressTargetPort: ingressTargetPort
    scaleSettings: {
      maxReplicas: scaleMaxReplicas
      minReplicas: scaleMinReplicas
    }
    secrets: union(
      [],
      map(secrets, secret => {
        name: secret.secretName // Use Key Vault secret name
        value: null // Value is not needed when using Key Vault references
        keyVaultUrl: secret.secretUri // Add Key Vault secret URI
        identity: userAssignedManagedIdentityResourceId
      })
    )
    containers: [
      {
        image: existingImage == '' ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' : existingImage
        name: 'main'
        resources: {
          cpu: json(cpu)
          memory: memory
        }
        volumeMounts: additionalVolumeMounts
        env: union(
          [
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
            secretRef: secret.secretName
          })
        )
        probes: probes
      }
    ]
    managedIdentities: {
      systemAssigned: false
      userAssignedResourceIds: [userAssignedManagedIdentityResourceId]
    }
    registries: [
      {
        server: containerRegistryLoginServer
        identity: userAssignedManagedIdentityResourceId
      }
    ]
    environmentResourceId: containerAppsEnvironmentResourceId
    location: location
    tags: union(tags, { 'azd-service-name': name })
    ingressExternal: ingressExternal
    volumes: additionalVolumes
    initContainersTemplate: initContainersTemplate
    authConfig: empty(authentication)
      ? null
      : {
          platform: {
            enabled: bool(authentication.enabled)
          }
          globalValidation: {
            redirectToProvider: 'azureactivedirectory'
            unauthenticatedClientAction: 'RedirectToLoginPage'
          }
          identityProviders: {
            azureActiveDirectory: {
              enabled: bool(authentication.enabled)
              registration: {
                clientId: authentication.clientId
                clientSecretSettingName: managedIdentityClientIdSecretName
                openIdIssuer: authentication.openIdIssuer
              }
              validation: {
                defaultAuthorizationPolicy: {
                  allowedApplications: []
                }
              }
            }
          }
        }
  }
}

output AZURE_RESOURCE_CONTAINER_APP_ID string = containerApp.outputs.resourceId
output AZURE_RESOURCE_CONTAINER_APP_FQDN string = 'https://${containerApp.outputs.fqdn}'
output AZURE_RESOURCE_CONTAINER_APP_AUTHENTICATION_CALLBACK_URI string = 'https://${containerApp.outputs.fqdn}/.auth/login/aad/callback'
