provider "azurerm" {
  features = {}
}

resource "azurerm_resource_group" "rg" {
  name     = "__TF_NAME__-rg"
  location = var.location
}

resource "azurerm_app_service_plan" "plan" {
  name                = "__TF_NAME__-plan"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku {
    tier = "Standard"
    size = var.app_service_sku
  }
}

resource "azurerm_app_service" "app" {
  name                = "__TF_NAME__-app"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  app_service_plan_id = azurerm_app_service_plan.plan.id

  site_config {
    linux_fx_version = "DOCKER|${var.container_image}"
  }
}

output "app_default_hostname" {
  value       = azurerm_app_service.app.default_site_hostname
  description = "App Service hostname"
}

variable "location" { default = "East US" }
variable "app_service_sku" { default = "B1" }
variable "container_image" { default = "" }