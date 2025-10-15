# Policy Outputs
output "policies_yaml" {
  description = "The policies_json variable rendered as YAML."
  value       = module.cloud_custodian_lambda.policies_yaml
}

output "mode_type" {
  description = "The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.)"
  value       = module.cloud_custodian_lambda.mode_type
}

# Package Information Outputs
output "package_versions" {
  description = "JSON string containing versions of all packages included in the Lambda deployment"
  value       = module.cloud_custodian_lambda.package_versions
}

output "sha256_hex" {
  description = "SHA256 hash of the Lambda package in hexadecimal format"
  value       = module.cloud_custodian_lambda.sha256_hex
}

# Lambda Function Outputs
output "lambda_function" {
  description = "Complete AWS Lambda function resource with all attributes"
  value       = try(module.cloud_custodian_lambda.lambda_function[local.region], null)
}

output "lambda_function_name" {
  description = "The name of the lambda function"
  value       = try(module.cloud_custodian_lambda.lambda_function_name[local.region], null)
}

output "lambda_function_tags" {
  description = "The name of the lambda function"
  value       = try(module.cloud_custodian_lambda.lambda_function_tags[local.region], null)
}

output "lambda_function_role" {
  description = "The IAM role used in the Lambda Function"
  value       = try(module.cloud_custodian_lambda.lambda_function_role[local.region], null)
}

output "lambda_function_source_code_hash" {
  description = "Base64-encoded representation of raw SHA-256 sum of the zip file"
  value       = try(module.cloud_custodian_lambda.lambda_function_source_code_hash[local.region], null)
}

# Periodic Mode Outputs
output "periodic_event_rule_name" {
  description = "The name of the CloudWatch Event Rule for periodic mode"
  value       = try(module.cloud_custodian_lambda.periodic_event_rule_name[local.region], null)
}

output "periodic_schedule_expression" {
  description = "The schedule expression for periodic mode"
  value       = try(module.cloud_custodian_lambda.periodic_schedule_expression[local.region], null)
}
