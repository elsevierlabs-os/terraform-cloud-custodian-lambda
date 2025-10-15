# Cloud custodian lambda mailer

A terraform module to create [cloud custodian lambda mailer](https://cloudcustodian.io/docs/tools/c7n-mailer.html). The user provides mailer config in either YAML or JSON format and based on this associated lambda resources are created and managed by terraform. Located in [modules/cloud-custodian-lambda-mailer](./modules/cloud-custodian-lambda-mailer).

## Managing Cloud Custodian Mailer

### Prerequisites

Depending on what notification endpoints you are using you will need different resources in AWS. See [c7n-mailer](https://cloudcustodian.io/docs/tools/c7n-mailer.html) for further details. At a minimum you will require an SQS queue and IAM role with `arn:aws:iam::aws:policy/AmazonSQSReadOnlyAccess` and `arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole` permissions.

### Terraform

```hcl
module "custodian_mailer" {
  source = "../../modules/cloud-custodian-lambda-mailer"

  mailer = <<-YAML
    queue_url: https://sqs.<region>.amazonaws.com/<account-no>/<sqs-queue>
    role: arn:aws:iam::<account-no>:role/<iam-role>
    from_address: <email-address>
  YAML
}
```

Also see [examples/mailer](../../examples/mailer).

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5.7 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.0 |
| <a name="requirement_external"></a> [external](#requirement\_external) | >= 2.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.13.0 |
| <a name="provider_external"></a> [external](#provider\_external) | 2.3.5 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_event_rule.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_lambda_function.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_permission.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_iam_role.custodian_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_role) | data source |
| [external_external.package_lambda](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |
| [external_external.validate_mailer](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_mailer"></a> [mailer](#input\_mailer) | Mailer configuration in JSON or YAML format | `string` | n/a | yes |
| <a name="input_architecture"></a> [architecture](#input\_architecture) | Architecture for the Lambda function. Allowed: arm64 or x86\_64. | `string` | `"arm64"` | no |
| <a name="input_force_deploy"></a> [force\_deploy](#input\_force\_deploy) | Force redeployment of Lambda function by updating a deployment timestamp tag.<br/>    Set to true to trigger redeployment when source\_code\_hash doesn't detect changes. | `bool` | `false` | no |
| <a name="input_templates"></a> [templates](#input\_templates) | Custom message templates folder location | `string` | `""` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_event_rule"></a> [event\_rule](#output\_event\_rule) | Complete AWS Cloudwatch Event Rule with all attributes |
| <a name="output_event_rule_arn"></a> [event\_rule\_arn](#output\_event\_rule\_arn) | The ARN of the CloudWatch Event Rule |
| <a name="output_event_rule_name"></a> [event\_rule\_name](#output\_event\_rule\_name) | The name of the CloudWatch Event Rule |
| <a name="output_event_rule_schedule_expression"></a> [event\_rule\_schedule\_expression](#output\_event\_rule\_schedule\_expression) | The schedule expression for the event |
| <a name="output_lambda_function"></a> [lambda\_function](#output\_lambda\_function) | Complete AWS Lambda function resource with all attributes |
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | The ARN of the Lambda Function |
| <a name="output_lambda_function_filename"></a> [lambda\_function\_filename](#output\_lambda\_function\_filename) | Location of the lambda zip file |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | The name of the lambda function |
| <a name="output_lambda_function_role"></a> [lambda\_function\_role](#output\_lambda\_function\_role) | The IAM role used in the Lambda Function |
| <a name="output_lambda_function_source_code_hash"></a> [lambda\_function\_source\_code\_hash](#output\_lambda\_function\_source\_code\_hash) | Base64-encoded representation of raw SHA-256 sum of the zip file |
| <a name="output_lambda_function_source_code_size"></a> [lambda\_function\_source\_code\_size](#output\_lambda\_function\_source\_code\_size) | The size in bytes of the function .zip file |
| <a name="output_mailer_config"></a> [mailer\_config](#output\_mailer\_config) | The validated mailer config with defaults |
| <a name="output_mailer_json"></a> [mailer\_json](#output\_mailer\_json) | The mailer variable rendered as JSON. |
| <a name="output_mailer_yaml"></a> [mailer\_yaml](#output\_mailer\_yaml) | The mailer variable rendered as YAML. |
| <a name="output_package_versions"></a> [package\_versions](#output\_package\_versions) | JSON string containing versions of all packages included in the Lambda deployment |
| <a name="output_region"></a> [region](#output\_region) | Regions that the mailer is deployed to |
| <a name="output_sha256_hex"></a> [sha256\_hex](#output\_sha256\_hex) | SHA256 hash of the Lambda package in hexadecimal format |
<!-- END_TF_DOCS -->