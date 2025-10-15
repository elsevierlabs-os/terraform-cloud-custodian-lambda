# ec2-instance-state

Configuration in this directory creates an example cloud custodian ec2-instance-state policy as a lambda.

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
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.7.0 |

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
| <a name="input_force_deploy"></a> [force\_deploy](#input\_force\_deploy) | Force redeployment of Lambda functions by updating a deployment timestamp tag.<br/>    Set to true to trigger redeployment when source\_code\_hash doesn't detect changes. | `bool` | `false` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cloudwatch_event_pattern"></a> [cloudwatch\_event\_pattern](#output\_cloudwatch\_event\_pattern) | The event pattern for event mode |
| <a name="output_cloudwatch_event_rule_name"></a> [cloudwatch\_event\_rule\_name](#output\_cloudwatch\_event\_rule\_name) | The name of the CloudWatch Event Rule for event mode |
| <a name="output_lambda_function"></a> [lambda\_function](#output\_lambda\_function) | The complete lambda function object for each region |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | The name of the lambda function |
| <a name="output_lambda_function_source_code_hash"></a> [lambda\_function\_source\_code\_hash](#output\_lambda\_function\_source\_code\_hash) | Base64-encoded representation of raw SHA-256 sum of the zip file |
| <a name="output_mode_type"></a> [mode\_type](#output\_mode\_type) | The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.) |
| <a name="output_policies_yaml"></a> [policies\_yaml](#output\_policies\_yaml) | The policies\_json variable rendered as YAML. |
<!-- END_TF_DOCS -->