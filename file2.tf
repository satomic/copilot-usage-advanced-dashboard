resource "azapi_resource" "openai_backend" {
  for_each  = { for endpoint in var.openai_endpoints : endpoint.key => endpoint }
  type      = "Microsoft.ApiManagement/service/backends@2024-05-01"
  parent_id = azurerm_api_management.api_management.id
  name      = each.value.name
  body = {
    properties = {
      circuitBreaker = {
        rules = [
          {
            acceptRetryAfter = true
            failureCondition = {
              count = 1
              errorReasons = [
                "timeout"
              ]
              interval = "PT1M"
              statusCodeRanges = [
                {
                  max = 429
                  min = 429
                }
              ]
            }
            name         = "breakerRule"
            tripDuration = "PT1M"
          }
        ]
      }
      description = "OpenAI Backend - ${each.value.name}"
      protocol    = "http"
      title       = "OpenAI Backend - ${each.value.name}"
      tls = {
        validateCertificateChain = true
        validateCertificateName  = true
      }
      type = "Single"
      url  = "${each.value.endpoint}openai/"
    }
  }
}

resource "azapi_resource" "openai_load_balanced_backend" {
  for_each  = { for pool in var.openai.pools : pool.name => pool }
  type      = "Microsoft.ApiManagement/service/backends@2024-05-01"
  parent_id = azurerm_api_management.api_management.id
  name      = each.key
  body = {
    properties = {
      description = each.key
      pool = {
        services = [
          for key, backend in var.openai_endpoints : {
            id       = "/subscriptions/${var.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.ApiManagement/service/${azurerm_api_management.api_management.name}/backends/${backend.name}"
            priority = backend.priority
          } if backend.pool_name == each.key
        ]
      }
      title = each.key
      type  = "Pool"
    }
  }
  depends_on                = [azapi_resource.openai_backend]
  schema_validation_enabled = false
}

resource "azurerm_api_management_backend" "openai_semantic_cache_embedding_backend" {
  api_management_name = azurerm_api_management.api_management.name
  resource_group_name = var.resource_group_name
  name                = var.openai_semantic_cache_embedding_backend_id
  url                 = "${var.openai_endpoints[0].endpoint}openai/deployments/${var.openai_semantic_cache_embedding_backend_deployment_name}/embeddings"
  protocol            = "http"
  title               = "OpenAI Semantic Cache Embedding Backend - ${var.openai_endpoints[0].endpoint}"
  description         = "OpenAI Semantic Cache Embedding Backend - ${var.openai_endpoints[0].endpoint}"
  tls {
    validate_certificate_chain = true
    validate_certificate_name  = true
  }
}