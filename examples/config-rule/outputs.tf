# Policy Outputs
output "policies_yaml" {
  description = "The policies_json variable rendered as YAML."
  value       = module.cloud_custodian_lambda.policies_yaml
}

output "mode_type" {
  description = "The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.)"
  value       = module.cloud_custodian_lambda.mode_type
}

# Lambda Function Outputs
output "lambda_function" {
  description = "The complete lambda function object for each region"
  value       = module.cloud_custodian_lambda.lambda_function
}

output "lambda_function_name" {
  description = "The name of the lambda function"
  value       = try(module.cloud_custodian_lambda.lambda_function_name[local.region], null)
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = try(module.cloud_custodian_lambda.lambda_function_arn[local.region], null)
}

# Config Rule Mode Outputs
output "config_rule" {
  description = "Complete AWS Config Rule resource with all attributes"
  value       = try(module.cloud_custodian_lambda.config_rule[local.region], null)
}

output "config_rule_name" {
  description = "The name of the AWS Config Rule"
  value       = try(module.cloud_custodian_lambda.config_rule_name[local.region], null)
}
