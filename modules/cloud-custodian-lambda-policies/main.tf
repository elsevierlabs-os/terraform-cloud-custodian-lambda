locals {
  policies_obj  = can(jsondecode(var.policies)) ? jsondecode(var.policies) : yamldecode(var.policies)
  policies_json = can(jsondecode(var.policies)) ? var.policies : jsonencode(yamldecode(var.policies))
  policy_names  = [for p in local.policies_obj.policies : p.name]
}

module "custodian_policy" {
  source = "../.."

  for_each = toset(local.policy_names)

  policies          = var.policies
  policy_name       = each.key
  execution_options = var.execution_options
  regions           = var.regions
  architecture      = var.architecture
  force_deploy      = var.force_deploy
}
