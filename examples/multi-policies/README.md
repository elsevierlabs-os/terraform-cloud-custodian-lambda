# Multiple Policies

Configuration in this directory creates multiple cloud-custodian policies as lambda.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5.7 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.14.1 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_cloud_custodian_s3"></a> [cloud\_custodian\_s3](#module\_cloud\_custodian\_s3) | terraform-aws-modules/s3-bucket/aws | n/a |
| <a name="module_custodian_policies"></a> [custodian\_policies](#module\_custodian\_policies) | ../../modules/cloud-custodian-lambda-policies | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_iam_role.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_regions"></a> [regions](#input\_regions) | Regions to deploy the policy to | `list(string)` | <pre>[<br/>  "eu-west-1",<br/>  "us-east-1",<br/>  "us-east-2"<br/>]</pre> | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | Lambda function ARNs for each policy-region combination |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | Lambda function names for each policy-region combination |
| <a name="output_mode_type"></a> [mode\_type](#output\_mode\_type) | Cloud Custodian mode type for each policy |
| <a name="output_policies"></a> [policies](#output\_policies) | Map of policy names to their complete module outputs |
| <a name="output_policies_yaml"></a> [policies\_yaml](#output\_policies\_yaml) | The policies rendered as YAML. |
| <a name="output_policy_names"></a> [policy\_names](#output\_policy\_names) | Names of all deployed policies |
| <a name="output_regions"></a> [regions](#output\_regions) | Regions where each policy is deployed |
<!-- END_TF_DOCS -->