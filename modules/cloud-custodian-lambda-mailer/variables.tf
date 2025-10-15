variable "mailer" {
  description = "Mailer configuration in JSON or YAML format"
  type        = string
  validation {
    condition     = can(jsondecode(var.mailer)) || can(yamldecode(var.mailer))
    error_message = "Must be valid JSON or YAML."
  }
}

variable "templates" {
  description = "Custom message templates folder location"
  type        = string
  default     = ""
}

variable "architecture" {
  description = "Architecture for the Lambda function. Allowed: arm64 or x86_64."
  type        = string
  default     = "arm64"
  validation {
    condition     = contains(["arm64", "x86_64"], var.architecture)
    error_message = "architecture must be either 'arm64' or 'x86_64'."
  }
}

variable "force_deploy" {
  description = <<EOT
    Force redeployment of Lambda function by updating a deployment timestamp tag.
    Set to true to trigger redeployment when source_code_hash doesn't detect changes.
  EOT
  type        = bool
  default     = false
}
