variable "create_bucket" {
  description = "Whether to create the S3 bucket for Cloud Custodian multi-policies outputs"
  type        = bool
  default     = true
}

variable "regions" {
  description = "Regions to deploy the policy to"
  type        = list(string)
  default     = ["eu-west-1", "us-east-1", "us-east-2"]
}
