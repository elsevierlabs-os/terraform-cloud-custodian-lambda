# Multiple Regions

Configuration in this directory creates the same cloud custodian policy as a lambda across multiple regions.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5.7 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.0 |
| <a name="requirement_external"></a> [external](#requirement\_external) | >= 1.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.14.1 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_cloud_custodian_lambda"></a> [cloud\_custodian\_lambda](#module\_cloud\_custodian\_lambda) | ../../ | n/a |
| <a name="module_cloud_custodian_s3"></a> [cloud\_custodian\_s3](#module\_cloud\_custodian\_s3) | terraform-aws-modules/s3-bucket/aws | n/a |

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
| <a name="output_lambda_function"></a> [lambda\_function](#output\_lambda\_function) | The complete lambda function object for each region |
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | The IAM role used in the Lambda Function |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | The name of the lambda function |
| <a name="output_mode_type"></a> [mode\_type](#output\_mode\_type) | The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.) |
| <a name="output_periodic_event_rule_name"></a> [periodic\_event\_rule\_name](#output\_periodic\_event\_rule\_name) | The name of the CloudWatch Event Rule for periodic mode |
| <a name="output_periodic_schedule_expression"></a> [periodic\_schedule\_expression](#output\_periodic\_schedule\_expression) | The schedule expression for periodic mode |
| <a name="output_policies_yaml"></a> [policies\_yaml](#output\_policies\_yaml) | The policies\_json variable rendered as YAML. |
| <a name="output_regions"></a> [regions](#output\_regions) | Regions that the policy is deployed to |
<!-- END_TF_DOCS -->