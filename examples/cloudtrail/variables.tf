variable "create_cloudtrail_s3_bucket" {
  description = "Whether to create the S3 bucket for Cloud Custodian cloudtrail outputs"
  type        = bool
  default     = true
}
