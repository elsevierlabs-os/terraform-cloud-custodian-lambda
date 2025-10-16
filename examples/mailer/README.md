# Mailer

Configuration in this directory creates an example cloud custodian mailer as a lambda.

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
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.12.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_cloud_custodian_lambda_mailer"></a> [cloud\_custodian\_lambda\_mailer](#module\_cloud\_custodian\_lambda\_mailer) | ../../modules/cloud-custodian-lambda-mailer | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_iam_role.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_region"></a> [region](#input\_region) | Regions to deploy the mailer to | `string` | `"eu-west-1"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_event_rule_name"></a> [event\_rule\_name](#output\_event\_rule\_name) | The name of the CloudWatch Event Rule for event mode |
| <a name="output_event_rule_schedule_expression"></a> [event\_rule\_schedule\_expression](#output\_event\_rule\_schedule\_expression) | The event pattern for event mode |
| <a name="output_lambda_function"></a> [lambda\_function](#output\_lambda\_function) | Complete AWS Lambda function resource with all attributes |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | The name of the lambda function |
| <a name="output_lambda_function_role"></a> [lambda\_function\_role](#output\_lambda\_function\_role) | The IAM role used in the Lambda Function |
| <a name="output_lambda_function_source_code_hash"></a> [lambda\_function\_source\_code\_hash](#output\_lambda\_function\_source\_code\_hash) | Base64-encoded representation of raw SHA-256 sum of the zip file |
| <a name="output_mailer_config"></a> [mailer\_config](#output\_mailer\_config) | The validated mailer\_json with defaults |
| <a name="output_mailer_yaml"></a> [mailer\_yaml](#output\_mailer\_yaml) | The mailer variable rendered as YAML. |
| <a name="output_package_versions"></a> [package\_versions](#output\_package\_versions) | JSON string containing versions of all packages included in the Lambda deployment |
| <a name="output_region"></a> [region](#output\_region) | Regions that the mailer is deployed to |
| <a name="output_sha256_hex"></a> [sha256\_hex](#output\_sha256\_hex) | SHA256 hash of the Lambda package in hexadecimal format |
<!-- END_TF_DOCS -->