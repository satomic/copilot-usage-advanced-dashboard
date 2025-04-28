param location string
param tags object
param abbrs object
param resourceToken string
param userAssignedIdentityPrincipalId string
param elasticSearchFileShareName string
param grafanaFileShareName string
param cpuadUpdaterFileShareName string
param keyVaultResourceId string
param containerAppsVirtualNetworkId string

var accessKey1Name = 'storageAccountKey1'

module storageAccount 'br/public:avm/res/storage/storage-account:0.18.2' = {
  name: 'storageAccount'
  params: {
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    skuName: 'Premium_LRS'
    kind: 'FileStorage'
    tags: tags
    secretsExportConfiguration: {
      keyVaultResourceId: keyVaultResourceId
      accessKey1Name: accessKey1Name
    }
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
      virtualNetworkRules: [
        {
          id: containerAppsVirtualNetworkId
          action: 'Allow'
        }
      ]
    }
    roleAssignments:[
      {
        principalId: userAssignedIdentityPrincipalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage File Data SMB Share Contributor'
      }
    ]
    fileServices: {
      shares: [
        {
          name: elasticSearchFileShareName
          shareQuota: 100
          enabledProtocols: 'NFS'
          provisionedThroughputInMiBps: 230
        }
        {
          name: grafanaFileShareName
          shareQuota: 100
          enabledProtocols: 'NFS'
          provisionedThroughputInMiBps: 230
        }
        {
          name: cpuadUpdaterFileShareName
          shareQuota: 100
          enabledProtocols: 'NFS'
          provisionedThroughputInMiBps: 230
        }
      ]
    }
    // The NFS protocol does not support encryption and relies on network-level security. This setting must be disabled for NFS to work.
    supportsHttpsTrafficOnly: false
  }
}

output AZURE_STORAGE_ACCOUNT_ID string = storageAccount.outputs.resourceId
output AZURE_STORAGE_ACCOUNT_NAME string = storageAccount.outputs.name
output AZURE_STORAGE_ELASTIC_SEARCH_FILE_SHARE_NAME string = elasticSearchFileShareName
output AZURE_STORAGE_GRAFANA_FILE_SHARE_NAME string = grafanaFileShareName
output AZURE_STORAGE_ACCOUNT_KEY_SECRET_NAME string = accessKey1Name
output AZURE_STORAGE_CPUAD_UPDATER_FILE_SHARE_NAME string = cpuadUpdaterFileShareName
