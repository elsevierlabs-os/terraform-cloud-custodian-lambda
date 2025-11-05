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

# EventBridge Scheduler Mode Outputs
output "eventbridge_schedule_name" {
  description = "The name of the EventBridge Schedule"
  value       = try(module.cloud_custodian_lambda.eventbridge_schedule_name[local.region], null)
}

output "eventbridge_schedule_group_name" {
  description = "The EventBridge Schedule group name"
  value       = try(module.cloud_custodian_lambda.eventbridge_schedule_group_name[local.region], null)
}

output "eventbridge_schedule_expression" {
  description = "The schedule expression for schedule mode"
  value       = try(module.cloud_custodian_lambda.eventbridge_schedule_expression[local.region], null)
}

output "eventbridge_schedule_timezone" {
  description = "The timezone for the schedule"
  value       = try(module.cloud_custodian_lambda.eventbridge_schedule_timezone[local.region], null)
}
