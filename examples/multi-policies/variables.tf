variable "regions" {
  description = "Regions to deploy the policy to"
  type        = list(string)
  default     = ["eu-west-1", "us-east-1", "us-east-2"]
}
