provider "aws" {
  region = var.aws_region
}

resource "aws_ecr_repository" "repo" {
  name = "__TF_NAME__-repo"
}

resource "aws_ecs_cluster" "cluster" {
  name = "__TF_NAME__-cluster"
}

resource "aws_ecs_task_definition" "task" {
  family = "__TF_NAME__-task"
  container_definitions = jsonencode([{
    name  = "__TF_NAME__-container"
    image = var.container_image
    portMappings = [{
      containerPort = __PORT__
      hostPort = __PORT__
      protocol = "tcp"
    }]
    essential = true
  }])
}

resource "aws_ecs_service" "service" {
  name = "__TF_NAME__-service"
  cluster = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.task.arn
  desired_count = var.desired_count
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.repo.repository_url
  description = "ECR repository URL"
}

output "ecs_cluster_id" {
  value       = aws_ecs_cluster.cluster.id
  description = "ECS cluster id"
}

output "ecs_service_name" {
  value       = aws_ecs_service.service.name
  description = "ECS service name"
}

variable "aws_region" { default = "us-east-1" }
variable "container_image" { default = "" }
variable "desired_count" { default = 1 }
variable "service_port" { default = __PORT__ }

