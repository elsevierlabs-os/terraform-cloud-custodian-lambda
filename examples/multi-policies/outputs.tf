output "policies_yaml" {
  description = "The policies rendered as YAML."
  value       = module.custodian_policies.policies_yaml
}

output "policy_names" {
  description = "Names of all deployed policies"
  value       = module.custodian_policies.policy_names
}

output "mode_type" {
  description = "Cloud Custodian mode type for each policy"
  value       = module.custodian_policies.mode_type
}

output "regions" {
  description = "Regions where each policy is deployed"
  value       = module.custodian_policies.regions
}

output "lambda_function_name" {
  description = "Lambda function names for each policy-region combination"
  value       = module.custodian_policies.lambda_function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARNs for each policy-region combination"
  value       = module.custodian_policies.lambda_function_arn
}

output "policies" {
  description = "Map of policy names to their complete module outputs"
  value       = module.custodian_policies.policies
}
