resource "azurerm_api_management_backend" "openai_backend" {
  for_each            = { for endpoint in var.openai_endpoints : endpoint.key => endpoint }
  api_management_name = azurerm_api_management.api_management.name
  resource_group_name = var.resource_group_name
  name                = each.value.name
  url                 = "${each.value.endpoint}openai/"
  protocol            = "http"
  title               = "OpenAI Backend - ${each.value.name}"
  description         = "OpenAI Backend - ${each.value.name}"
  tls {
    validate_certificate_chain = true
    validate_certificate_name  = true
  }
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