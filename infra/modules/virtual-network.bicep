param location string
param abbrs object
param resourceToken string

module containerAppsNetworkSecurityGroup 'br/public:avm/res/network/network-security-group:0.5.1' = {
  name: 'container-apps-network-security-group'
  params: {
    name: '${abbrs.networkNetworkSecurityGroups}${resourceToken}'
    location: location
    securityRules: [
      {
        name: 'AllowNFSOutbound'
        properties: {
          access: 'Allow'
          direction: 'Outbound'
          priority: 100
          protocol: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          sourcePortRange: '*'
          destinationAddressPrefix: 'Storage'
          destinationPortRanges: [
            '445'
            '2049'
          ]
        }
      }
    ]
  }  
}

module virtualNetwork 'br/public:avm/res/network/virtual-network:0.6.1' = {
  name: 'name'
  params: {
    addressPrefixes: ['10.0.0.0/27']
    name: '${abbrs.networkVirtualNetworks}${resourceToken}'
    location: location
    subnets: [
      {
        name: 'container-apps'
        addressPrefix: '10.0.0.0/27'
        delegation: 'Microsoft.App/environments'
        serviceEndpoints: [
          'Microsoft.Storage'
        ]
        networkSecurityGroupResourceId: containerAppsNetworkSecurityGroup.outputs.resourceId
      }
    ]    
  }
}


output AZURE_VIRTUAL_NETWORK_ID string = virtualNetwork.outputs.resourceId
output AZURE_VIRTUAL_NETWORK_NAME string = virtualNetwork.outputs.name
output AZURE_VIRTUAL_NETWORK_CONTAINER_APPS_SUBNET_ID string = virtualNetwork.outputs.subnetResourceIds[0]
