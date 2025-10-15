# Policy Outputs
output "policy_name" {
  description = "The name of the policy being deployed (if policy_name was specified)"
  value       = var.policy_name != "" ? var.policy_name : null
}

output "policies_yaml" {
  description = "The policies rendered as YAML (only the specific policy if policy_name is set)"
  value       = var.policy_name != "" ? yamlencode({ "policies" : [local.policy_obj] }) : (!can(jsondecode(var.policies)) ? var.policies : yamlencode(local.policies_obj))
}

output "policies_json" {
  description = "The policies rendered as JSON (only the specific policy if policy_name is set)"
  value       = var.policy_name != "" ? jsonencode({ "policies" : [local.policy_obj] }) : local.policies_json
}

output "regions" {
  description = "Regions that the policy is deployed to"
  value       = local.regions
}

output "mode_type" {
  description = "The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.)"
  value       = local.mode_type
}

# Package Information Outputs
output "package_lambda_result" {
  description = "Full output from package lambda step"
  value       = try(data.external.package_lambda.result, null)
}

output "package_versions" {
  description = "JSON string containing versions of all packages included in the Lambda deployment"
  value       = try(data.external.package_lambda.result["package_versions"], null)
}

output "sha256_hex" {
  description = "SHA256 hash of the Lambda package in hexadecimal format"
  value       = try(data.external.package_lambda.result["sha256_hex"], null)
}

# Lambda Function Outputs
output "lambda_function" {
  description = "Complete AWS Lambda function resource with all attributes"
  value       = aws_lambda_function.custodian
}

output "lambda_function_name" {
  description = "Map of Lambda function names by region"
  value       = { for region, func in aws_lambda_function.custodian : region => func.function_name }
}

output "lambda_function_tags" {
  description = "Map of Lambda function tags by region"
  value       = { for region, func in aws_lambda_function.custodian : region => func.tags }
}

output "lambda_function_arn" {
  description = "Map of Lambda function ARNs by region"
  value       = { for region, func in aws_lambda_function.custodian : region => func.arn }
}

output "lambda_function_source_code_hash" {
  description = "Map of Lambda function source code hashes by region"
  value       = { for region, func in aws_lambda_function.custodian : region => func.source_code_hash }
}

output "lambda_function_source_code_size" {
  description = "Map of Lambda function source code sizes by region"
  value       = { for region, func in aws_lambda_function.custodian : region => func.source_code_size }
}

output "lambda_function_role" {
  description = "Map of Lambda function IAM roles by region"
  value       = { for region, func in aws_lambda_function.custodian : region => func.role }
}

output "lambda_function_filename" {
  description = "Map of Lambda function filenames by region"
  value       = { for region, func in aws_lambda_function.custodian : region => func.filename }
}

# Periodic Mode Outputs
output "periodic_event_rule" {
  description = "Complete AWS Cloudwatch Event Rule for periodic resource with all attributes"
  value       = local.periodic ? aws_cloudwatch_event_rule.periodic : {}
}

output "periodic_event_rule_name" {
  description = "The name of the CloudWatch Event Rule for periodic mode"
  value       = local.periodic ? { for region, rule in aws_cloudwatch_event_rule.periodic : region => rule.name } : {}
}

output "periodic_event_rule_arn" {
  description = "The ARN of the CloudWatch Event Rule for periodic mode"
  value       = local.periodic ? { for region, rule in aws_cloudwatch_event_rule.periodic : region => rule.arn } : {}
}

output "periodic_schedule_expression" {
  description = "The schedule expression for periodic mode"
  value       = local.periodic ? { for region, rule in aws_cloudwatch_event_rule.periodic : region => rule.schedule_expression } : {}
}

# CloudWatch Event Mode Outputs
output "cloudwatch_event_rule" {
  description = "Complete AWS Cloudwatch Event Rule for cloudwatch event resource with all attributes"
  value       = local.cloudwatch_event ? aws_cloudwatch_event_rule.cloudwatch_event : {}
}

output "cloudwatch_event_rule_name" {
  description = "The name of the CloudWatch Event Rule for event mode"
  value       = local.cloudwatch_event ? { for region, rule in aws_cloudwatch_event_rule.cloudwatch_event : region => rule.name } : {}
}

output "cloudwatch_event_rule_arn" {
  description = "The ARN of the CloudWatch Event Rule for event mode"
  value       = local.cloudwatch_event ? { for region, rule in aws_cloudwatch_event_rule.cloudwatch_event : region => rule.arn } : {}
}

output "cloudwatch_event_pattern" {
  description = "The event pattern for event mode"
  value       = local.cloudwatch_event ? { for region, rule in aws_cloudwatch_event_rule.cloudwatch_event : region => rule.event_pattern } : {}
}

# Config Rule Mode Outputs
output "config_rule" {
  description = "Complete AWS Config Rule resource with all attributes"
  value       = local.config_rule ? aws_config_config_rule.config_rule : {}
}

output "config_rule_name" {
  description = "The name of the AWS Config Rule"
  value       = local.config_rule ? { for region, rule in aws_config_config_rule.config_rule : region => rule.name } : {}
}

output "config_rule_arn" {
  description = "The ARN of the AWS Config Rule"
  value       = local.config_rule ? { for region, rule in aws_config_config_rule.config_rule : region => rule.arn } : {}
}

output "config_rule_rule_id" {
  description = "The ID of the AWS Config Rule"
  value       = local.config_rule ? { for region, rule in aws_config_config_rule.config_rule : region => rule.rule_id } : {}
}
