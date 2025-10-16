# Policy Outputs
output "policies_yaml" {
  description = "The policies_json variable rendered as YAML."
  value       = module.cloud_custodian_lambda.policies_yaml
}

output "mode_type" {
  description = "The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.)"
  value       = module.cloud_custodian_lambda.mode_type
}

output "regions" {
  description = "Regions that the policy is deployed to"
  value       = module.cloud_custodian_lambda.regions
}

# Lambda Function Outputs
output "lambda_function" {
  description = "The complete lambda function object for each region"
  value       = module.cloud_custodian_lambda.lambda_function
}

output "lambda_function_name" {
  description = "The name of the lambda function"
  value       = module.cloud_custodian_lambda.lambda_function_name
}

output "lambda_function_arn" {
  description = "The IAM role used in the Lambda Function"
  value       = module.cloud_custodian_lambda.lambda_function_arn
}

# Periodic Mode Outputs
output "periodic_event_rule_name" {
  description = "The name of the CloudWatch Event Rule for periodic mode"
  value       = module.cloud_custodian_lambda.periodic_event_rule_name
}

output "periodic_schedule_expression" {
  description = "The schedule expression for periodic mode"
  value       = module.cloud_custodian_lambda.periodic_schedule_expression
}
