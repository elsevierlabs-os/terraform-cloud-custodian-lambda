# Cloud Custodian Lambda Operations Scripts

Python scripts called by Terraform `external` data sources to validate, package, and configure Cloud Custodian Lambda functions.

## Usage

Scripts are called by Terraform via `external` data sources:

```hcl
data "external" "validate_policy" {
  program = ["python3", "${path.module}/ops/validate_lambda_policy.py"]
  query = {
    policies    = var.policies
    policy_name = var.policy_name
  }
}
```
