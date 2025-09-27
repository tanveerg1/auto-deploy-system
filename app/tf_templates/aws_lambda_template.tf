# AWS Lambda + API Gateway (HTTP API v2) template for __TF_NAME__
provider "aws" {
  region = var.aws_region
}

# IAM role for Lambda with basic execution permissions
resource "aws_iam_role" "lambda" {
  name = var.function_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# The Lambda function - expects a zip file present at var.lambda_zip_path (e.g. artifact.zip)
resource "aws_lambda_function" "function" {
  filename         = var.lambda_zip_path
  function_name    = var.function_name
  role             = aws_iam_role.lambda.arn
  handler          = var.handler
  runtime          = var.runtime
  memory_size      = var.memory_size
  timeout          = var.timeout
  environment {
    variables = var.environment
  }

  # ensures Terraform notices code changes (file must exist when running apply)
  source_code_hash = filebase64sha256(var.lambda_zip_path)
}

# HTTP API (API Gateway v2) + Lambda integration
resource "aws_apigatewayv2_api" "api" {
  name          = "${var.function_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.function.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id   = aws_apigatewayv2_api.api.id
  route_key = "$default"
  target   = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id     = aws_apigatewayv2_api.api.id
  name       = "$default"
  auto_deploy = true
}

# Allow API Gateway to invoke the Lambda
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.function.arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# Useful outputs
output "api_endpoint" {
  value       = aws_apigatewayv2_api.api.api_endpoint
  description = "HTTP API endpoint (invoke URL)"
}

output "lambda_function_name" {
  value       = aws_lambda_function.function.function_name
  description = "Lambda function name"
}

output "lambda_arn" {
  value       = aws_lambda_function.function.arn
  description = "Lambda ARN"
}

# Variables
variable "aws_region" { default = "us-east-1" }

# function name should be provided by caller (generate_infra prompts); default here uses __TF_NAME__
variable "function_name" { default = "__TF_NAME__-fn" }

variable "runtime" { default = "python3.10" }
variable "handler" { default = "app.lambda_handler" }
variable "lambda_zip_path" { default = "artifact.zip" } # path relative to terraform working dir (deployer writes artifact.zip here)
variable "memory_size" { default = 128 }
variable "timeout" { default = 10 }
variable "environment" { 
  type = map(string)
  default = {} 
}