variable "create_bucket" {
  description = "Whether to create the S3 bucket for Cloud Custodian results"
  type        = bool
  default     = true
}

variable "force_deploy" {
  description = <<EOT
    Force redeployment of Lambda functions by updating a deployment timestamp tag.
    Set to true to trigger redeployment when source_code_hash doesn't detect changes.
  EOT
  type        = bool
  default     = false
}
