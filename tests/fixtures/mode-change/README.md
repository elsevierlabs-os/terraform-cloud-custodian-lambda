# Mode Change

This terraform allows us to validate that you can change the mode of a policy. See [mode_change_test.go](../../terraform/mode_change_test.go)

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
| <a name="module_cloud_custodian_lambda"></a> [cloud\_custodian\_lambda](#module\_cloud\_custodian\_lambda) | ../../../ | n/a |

## Resources

| Name | Type |
| ---- | ---- |
| [aws_iam_role.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_mode_type"></a> [mode\_type](#input\_mode\_type) | Cloud Custodian mode to deploy the policy in | `string` | n/a | yes |
| <a name="input_policy_name"></a> [policy\_name](#input\_policy\_name) | Name of the policy, made unique per test run so concurrent runs do not collide | `string` | n/a | yes |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_cloudwatch_event_pattern"></a> [cloudwatch\_event\_pattern](#output\_cloudwatch\_event\_pattern) | The event pattern for event mode |
| <a name="output_cloudwatch_event_rule_arn"></a> [cloudwatch\_event\_rule\_arn](#output\_cloudwatch\_event\_rule\_arn) | The ARN of the CloudWatch Event Rule for event mode |
| <a name="output_cloudwatch_event_rule_name"></a> [cloudwatch\_event\_rule\_name](#output\_cloudwatch\_event\_rule\_name) | The name of the CloudWatch Event Rule for event mode |
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | The ARN of the lambda function |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | The name of the lambda function |
| <a name="output_mode_type"></a> [mode\_type](#output\_mode\_type) | The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.) |
| <a name="output_periodic_event_rule_arn"></a> [periodic\_event\_rule\_arn](#output\_periodic\_event\_rule\_arn) | The ARN of the CloudWatch Event Rule for periodic mode |
| <a name="output_periodic_event_rule_name"></a> [periodic\_event\_rule\_name](#output\_periodic\_event\_rule\_name) | The name of the CloudWatch Event Rule for periodic mode |
| <a name="output_periodic_schedule_expression"></a> [periodic\_schedule\_expression](#output\_periodic\_schedule\_expression) | The schedule expression for periodic mode |
<!-- END_TF_DOCS -->