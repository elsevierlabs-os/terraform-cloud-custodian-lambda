output "policy_names" {
  description = "List of policy names"
  value       = local.policy_names
}

output "policies_yaml" {
  description = "The policies rendered as YAML."
  value       = !can(jsondecode(var.policies)) ? var.policies : yamlencode(var.policies)
}

output "policies_json" {
  description = "The policies rendered as JSON."
  value       = local.policies_json
}

output "regions" {
  description = "Map of policy names to their deployed regions"
  value = {
    for name, policy in module.custodian_policy :
    name => policy.regions
  }
}

output "mode_type" {
  description = "Map of policy names to their Cloud Custodian mode types"
  value = {
    for name, policy in module.custodian_policy :
    name => policy.mode_type
  }
}

output "lambda_function_arn" {
  description = "Map of policy names to Lambda function ARNs by region"
  value = {
    for name, policy in module.custodian_policy :
    name => policy.lambda_function_arn
  }
}

output "lambda_function_name" {
  description = "Map of policy names to Lambda function names by region"
  value = {
    for name, policy in module.custodian_policy :
    name => policy.lambda_function_name
  }
}

output "policies" {
  description = "Map of policy names to their complete module outputs"
  value       = module.custodian_policy
}
