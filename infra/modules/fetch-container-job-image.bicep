param exists bool
param name string

resource existingApp 'Microsoft.App/jobs@2024-03-01' existing = if (exists) {
  name: name
}

output containers array = exists ? existingApp.properties.template.containers : []
