# Mailer Outputs
output "mailer_yaml" {
  description = "The mailer variable rendered as YAML."
  value       = module.cloud_custodian_lambda_mailer.mailer_yaml
}

output "mailer_config" {
  description = "The validated mailer_json with defaults"
  value       = module.cloud_custodian_lambda_mailer.mailer_config
}

output "region" {
  description = "Regions that the mailer is deployed to"
  value       = module.cloud_custodian_lambda_mailer.region
}

# Lambda Function Outputs
output "lambda_function" {
  description = "Complete AWS Lambda function resource with all attributes"
  value       = module.cloud_custodian_lambda_mailer.lambda_function
}

output "lambda_function_name" {
  description = "The name of the lambda function"
  value       = module.cloud_custodian_lambda_mailer.lambda_function_name
}

output "lambda_function_role" {
  description = "The IAM role used in the Lambda Function"
  value       = module.cloud_custodian_lambda_mailer.lambda_function_role
}

output "lambda_function_source_code_hash" {
  description = "Base64-encoded representation of raw SHA-256 sum of the zip file"
  value       = module.cloud_custodian_lambda_mailer.lambda_function_source_code_hash
}

# CloudWatch Event Mode Outputs
output "event_rule_name" {
  description = "The name of the CloudWatch Event Rule for event mode"
  value       = module.cloud_custodian_lambda_mailer.event_rule_name
}

output "event_rule_schedule_expression" {
  description = "The event pattern for event mode"
  value       = module.cloud_custodian_lambda_mailer.event_rule_schedule_expression
}

# Package Information Outputs
output "package_versions" {
  description = "JSON string containing versions of all packages included in the Lambda deployment"
  value       = module.cloud_custodian_lambda_mailer.package_versions
  sensitive   = false
}

output "sha256_hex" {
  description = "SHA256 hash of the Lambda package in hexadecimal format"
  value       = module.cloud_custodian_lambda_mailer.sha256_hex
}
