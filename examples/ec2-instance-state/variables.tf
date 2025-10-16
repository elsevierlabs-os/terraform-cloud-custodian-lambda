variable "force_deploy" {
  description = <<EOT
    Force redeployment of Lambda functions by updating a deployment timestamp tag.
    Set to true to trigger redeployment when source_code_hash doesn't detect changes.
  EOT
  type        = bool
  default     = false
}
