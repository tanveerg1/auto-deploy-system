provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

resource "google_cloud_run_service" "service" {
  name     = "__TF_NAME__-svc"
  location = var.gcp_region
  template {
    spec {
      containers {
        image = var.container_image
        ports { container_port = __PORT__ }
      }
    }
  }
}

output "cloud_run_url" {
  value       = google_cloud_run_service.service.status[0].url
  description = "Cloud Run service URL"
}

variable "gcp_project" {}
variable "gcp_region" { default = "us-central1" }
variable "container_image" { default = "" }