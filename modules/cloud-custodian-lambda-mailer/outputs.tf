# Mailer Outputs
output "mailer_yaml" {
  description = "The mailer variable rendered as YAML."
  value       = !can(jsondecode(var.mailer)) ? var.mailer : yamlencode(jsondecode(local.mailer_json))
}

output "mailer_json" {
  description = "The mailer variable rendered as JSON."
  value       = local.mailer_json
}

output "mailer_config" {
  description = "The validated mailer config with defaults"
  value       = local.mailer_config
}

output "region" {
  description = "Regions that the mailer is deployed to"
  value       = local.region
}

# Lambda Function Outputs
output "lambda_function" {
  description = "Complete AWS Lambda function resource with all attributes"
  value       = aws_lambda_function.custodian
}

output "lambda_function_name" {
  description = "The name of the lambda function"
  value       = aws_lambda_function.custodian.function_name
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = aws_lambda_function.custodian.arn
}

output "lambda_function_source_code_hash" {
  description = "Base64-encoded representation of raw SHA-256 sum of the zip file"
  value       = aws_lambda_function.custodian.source_code_hash
}

output "lambda_function_source_code_size" {
  description = "The size in bytes of the function .zip file"
  value       = aws_lambda_function.custodian.source_code_size
}

output "lambda_function_role" {
  description = "The IAM role used in the Lambda Function"
  value       = aws_lambda_function.custodian.role
}

output "lambda_function_filename" {
  description = "Location of the lambda zip file"
  value       = aws_lambda_function.custodian.filename
}

# Event Outputs
output "event_rule" {
  description = "Complete AWS Cloudwatch Event Rule with all attributes"
  value       = aws_cloudwatch_event_rule.custodian
}

output "event_rule_name" {
  description = "The name of the CloudWatch Event Rule"
  value       = aws_cloudwatch_event_rule.custodian.name
}

output "event_rule_arn" {
  description = "The ARN of the CloudWatch Event Rule"
  value       = aws_cloudwatch_event_rule.custodian.arn
}

output "event_rule_schedule_expression" {
  description = "The schedule expression for the event"
  value       = aws_cloudwatch_event_rule.custodian.schedule_expression
}

# Package Information Outputs
output "package_versions" {
  description = "JSON string containing versions of all packages included in the Lambda deployment"
  value       = try(data.external.package_lambda.result["package_versions"], null)
}

output "sha256_hex" {
  description = "SHA256 hash of the Lambda package in hexadecimal format"
  value       = try(data.external.package_lambda.result["sha256_hex"], null)
}
