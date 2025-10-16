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

# CloudWatch Event Mode Outputs
output "cloudwatch_event_rule_name" {
  description = "The name of the CloudWatch Event Rule for event mode"
  value       = try(module.cloud_custodian_lambda.cloudwatch_event_rule_name[local.region], null)
}

output "cloudwatch_event_pattern" {
  description = "The event pattern for event mode"
  value       = try(module.cloud_custodian_lambda.cloudwatch_event_pattern[local.region], null)
}
