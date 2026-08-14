@description('azd 환경 이름')
param environmentName string

@description('리소스 위치')
param location string

@description('공통 태그')
param tags object

@secure()
@description('NEIS Open API 인증 키')
param neisApiKey string

@description('NEIS Open API 베이스 URL')
param neisBaseUrl string

var resourceToken = toLower(uniqueString(subscription().id, resourceGroup().id, environmentName))

// ---------- 로그 ----------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${resourceToken}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ---------- 컨테이너 레지스트리 ----------
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'acr${resourceToken}'
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
  }
}

// 컨테이너 앱이 ACR에서 이미지를 당겨올 수 있도록 하는 사용자 할당 ID
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${resourceToken}'
  location: location
  tags: tags
}

var acrPullRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, identity.id, acrPullRoleId)
  scope: containerRegistry
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleId
  }
}

// ---------- Container Apps 환경 ----------
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${resourceToken}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// 초기 프로비저닝용 플레이스홀더 이미지. 실제 이미지는 azd deploy가 교체한다.
var placeholderImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// ---------- 백엔드 앱 ----------
resource backendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-backend-${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'backend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: identity.id
        }
      ]
      secrets: [
        {
          name: 'neis-api-key'
          value: neisApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: placeholderImage
          env: [
            { name: 'NEIS_BASE_URL', value: neisBaseUrl }
            { name: 'NEIS_API_KEY', secretRef: 'neis-api-key' }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
  dependsOn: [acrPull]
}

// ---------- 프론트엔드 앱 ----------
resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-frontend-${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'frontend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: placeholderImage
          env: [
            // nginx가 /api 요청을 백엔드로 프록시할 대상
            { name: 'BACKEND_URL', value: 'https://${backendApp.properties.configuration.ingress.fqdn}' }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
  dependsOn: [acrPull]
}

// ---------- MCP 서버 앱 ----------
resource mcpApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-mcp-${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'mcp' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8001
        transport: 'auto'
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: identity.id
        }
      ]
      secrets: [
        {
          name: 'neis-api-key'
          value: neisApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'mcp'
          image: placeholderImage
          env: [
            { name: 'NEIS_BASE_URL', value: neisBaseUrl }
            { name: 'NEIS_API_KEY', secretRef: 'neis-api-key' }
            { name: 'MCP_HOST', value: '0.0.0.0' }
            { name: 'MCP_PORT', value: '8001' }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
  dependsOn: [acrPull]
}

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output BACKEND_URI string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output FRONTEND_URI string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output MCP_URI string = 'https://${mcpApp.properties.configuration.ingress.fqdn}/mcp'
