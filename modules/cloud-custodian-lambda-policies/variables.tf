variable "policies" {
  description = <<EOT
    Multi-policy configuration in JSON or YAML format with multiple policies.
    Note: The 'vars' section with YAML anchors/aliases is only supported in YAML format.
  EOT
  type        = string
  validation {
    condition     = can(jsondecode(var.policies)) || can(yamldecode(var.policies))
    error_message = "Must be valid JSON or YAML."
  }
}

variable "execution_options" {
  description = <<EOT
    Execution options for the AWS Lambda functions.
    Note that these are execution-options that would be set via the CLI when running `custodian run`.
    You can also set a more wide range of execution-options within the policy.
    See: https://cloudcustodian.io/docs/aws/lambda.html#execution-options
  EOT
  type        = map(any)
  default     = {}
}

variable "regions" {
  description = "List of AWS regions to deploy policies to. If empty, will use regions from policy configuration."
  type        = list(string)
  default     = ["us-east-1"]

  validation {
    condition = alltrue([
      for r in var.regions : can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", r))
    ])
    error_message = "All regions must be valid AWS region format (e.g., us-east-1, eu-west-2)"
  }
}

variable "architecture" {
  description = "Architecture for the Lambda functions. Allowed: arm64 or x86_64."
  type        = string
  default     = "arm64"
  validation {
    condition     = contains(["arm64", "x86_64"], var.architecture)
    error_message = "architecture must be either 'arm64' or 'x86_64'."
  }
}

variable "force_deploy" {
  description = <<EOT
    Force redeployment of Lambda functions by updating a deployment timestamp tag.
    Set to true to trigger redeployment when source_code_hash doesn't detect changes.
  EOT
  type        = bool
  default     = false
}
