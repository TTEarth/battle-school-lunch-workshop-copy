targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('azd 환경 이름')
param environmentName string

@minLength(1)
@description('리소스 배포 위치')
param location string

@secure()
@description('NEIS Open API 인증 키')
param neisApiKey string = ''

@description('NEIS Open API 베이스 URL')
param neisBaseUrl string = 'https://open.neis.go.kr'

var tags = { 'azd-env-name': environmentName }

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module resources 'resources.bicep' = {
  name: 'resources'
  scope: rg
  params: {
    environmentName: environmentName
    location: location
    tags: tags
    neisApiKey: neisApiKey
    neisBaseUrl: neisBaseUrl
  }
}

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.AZURE_CONTAINER_REGISTRY_ENDPOINT
output AZURE_RESOURCE_GROUP string = rg.name
output BACKEND_URI string = resources.outputs.BACKEND_URI
output FRONTEND_URI string = resources.outputs.FRONTEND_URI
output MCP_URI string = resources.outputs.MCP_URI
