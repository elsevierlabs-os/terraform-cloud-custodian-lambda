# Schedule

Configuration in this directory creates an example cloud custodian schedule policy as a lambda.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5.7 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.0 |
| <a name="requirement_external"></a> [external](#requirement\_external) | >= 2.0 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 6.0 |

## Modules

| Name | Source | Version |
| ---- | ------ | ------- |
| <a name="module_cloud_custodian_lambda"></a> [cloud\_custodian\_lambda](#module\_cloud\_custodian\_lambda) | ../../ | n/a |
| <a name="module_cloud_custodian_s3"></a> [cloud\_custodian\_s3](#module\_cloud\_custodian\_s3) | terraform-aws-modules/s3-bucket/aws | n/a |

## Resources

| Name | Type |
| ---- | ---- |
| [aws_iam_role.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.scheduler](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.scheduler](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_scheduler_schedule_group.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/scheduler_schedule_group) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.scheduler](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_create_bucket"></a> [create\_bucket](#input\_create\_bucket) | Whether to create the S3 bucket for Cloud Custodian results | `bool` | `true` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_eventbridge_schedule_expression"></a> [eventbridge\_schedule\_expression](#output\_eventbridge\_schedule\_expression) | The schedule expression for schedule mode |
| <a name="output_eventbridge_schedule_group_name"></a> [eventbridge\_schedule\_group\_name](#output\_eventbridge\_schedule\_group\_name) | The EventBridge Schedule group name |
| <a name="output_eventbridge_schedule_name"></a> [eventbridge\_schedule\_name](#output\_eventbridge\_schedule\_name) | The name of the EventBridge Schedule |
| <a name="output_eventbridge_schedule_timezone"></a> [eventbridge\_schedule\_timezone](#output\_eventbridge\_schedule\_timezone) | The timezone for the schedule |
| <a name="output_lambda_function"></a> [lambda\_function](#output\_lambda\_function) | The complete lambda function object for each region |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | The name of the lambda function |
| <a name="output_mode_type"></a> [mode\_type](#output\_mode\_type) | The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.) |
| <a name="output_policies_yaml"></a> [policies\_yaml](#output\_policies\_yaml) | The policies\_json variable rendered as YAML. |
<!-- END_TF_DOCS -->