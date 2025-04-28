param location string
param abbrs object
param resourceToken string

module identity 'br/public:avm/res/managed-identity/user-assigned-identity:0.2.1' = {
  name: 'identity'
  params: {
    name: '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
    location: location
  }
}

output AZURE_RESOURCE_USER_ASSIGNED_IDENTITY_ID string = identity.outputs.resourceId
output AZURE_RESOURCE_USER_ASSIGNED_IDENTITY_CLIENT_ID string = identity.outputs.clientId
output AZURE_RESOURCE_USER_ASSIGNED_IDENTITY_PRINCIPAL_ID string = identity.outputs.principalId
