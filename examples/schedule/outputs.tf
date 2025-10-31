output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.custodian_policy.lambda_function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.custodian_policy.lambda_function_arn
}

output "eventbridge_schedule_name" {
  description = "Name of the EventBridge Schedule"
  value       = module.custodian_policy.eventbridge_schedule_name
}

output "eventbridge_schedule_group_name" {
  description = "EventBridge Schedule group name"
  value       = module.custodian_policy.eventbridge_schedule_group_name
}
