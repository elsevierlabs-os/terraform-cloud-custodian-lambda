# Cloud custodian lambda policies

A terraform module to create multiple [cloud custodian lambda policies](https://cloudcustodian.io/docs/aws/lambda.html) across multiple regions. The user provides multiple policies in either YAML or JSON format and based on this associated lambda resources are created and managed by terraform. Note: The `vars` section with YAML anchors/aliases is only supported in YAML format. Using this module allows you to use vars across multiple policies. 

## Terraform

The example below deploys two policies using YAML with vars and anchors. The policies filter on images that are over 7 days old, `ami-age` shows AMIs that match the filter, `ec2-ami-age` shows running EC2 instances running AMIs that match the filter:

```hcl
module "custodian_policies" {
  source = "../../modules/cloud-custodian-lambda-policies"

  regions = ["us-east-1", "eu-west-1"]

  policies = <<-YAML
    vars:
      image-age-filters: &image-age-filters
        - type: image-age
          days: 7
    
    policies:
    - name: ami-age
      mode:
        type: periodic
        schedule: cron(0 11 ? * 3 *)
        role: "<your-iam-role>"
      resource: ami
      filters:
      - and: *image-age-filters
    
    - name: ec2-ami-age
      mode:
        type: periodic
        schedule: cron(0 11 ? * 3 *)
        role: "<your-iam-role>"
      resource: ec2
      filters:
      - and: *image-age-filters
      - "State.Name": "running"
  YAML
}
```

See the [examples/multi-policies](../../examples/multi-policies) directory for a complete working example.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5.7 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.0 |
| <a name="requirement_external"></a> [external](#requirement\_external) | >= 2.0 |

## Providers

No providers.

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_custodian_policy"></a> [custodian\_policy](#module\_custodian\_policy) | ../.. | n/a |

## Resources

No resources.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_policies"></a> [policies](#input\_policies) | Multi-policy configuration in JSON or YAML format with multiple policies.<br/>    Note: The 'vars' section with YAML anchors/aliases is only supported in YAML format. | `string` | n/a | yes |
| <a name="input_architecture"></a> [architecture](#input\_architecture) | Architecture for the Lambda functions. Allowed: arm64 or x86\_64. | `string` | `"arm64"` | no |
| <a name="input_execution_options"></a> [execution\_options](#input\_execution\_options) | Execution options for the AWS Lambda functions.<br/>    Note that these are execution-options that would be set via the CLI when running `custodian run`.<br/>    You can also set a more wide range of execution-options within the policy.<br/>    See: https://cloudcustodian.io/docs/aws/lambda.html#execution-options | `map(any)` | `{}` | no |
| <a name="input_force_deploy"></a> [force\_deploy](#input\_force\_deploy) | Force redeployment of Lambda functions by updating a deployment timestamp tag.<br/>    Set to true to trigger redeployment when source\_code\_hash doesn't detect changes. | `bool` | `false` | no |
| <a name="input_regions"></a> [regions](#input\_regions) | List of AWS regions to deploy policies to. If empty, will use regions from policy configuration. | `list(string)` | <pre>[<br/>  "us-east-1"<br/>]</pre> | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | Map of policy names to Lambda function ARNs by region |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | Map of policy names to Lambda function names by region |
| <a name="output_mode_type"></a> [mode\_type](#output\_mode\_type) | Map of policy names to their Cloud Custodian mode types |
| <a name="output_policies"></a> [policies](#output\_policies) | Map of policy names to their complete module outputs |
| <a name="output_policies_json"></a> [policies\_json](#output\_policies\_json) | The policies rendered as JSON. |
| <a name="output_policies_yaml"></a> [policies\_yaml](#output\_policies\_yaml) | The policies rendered as YAML. |
| <a name="output_policy_names"></a> [policy\_names](#output\_policy\_names) | List of policy names |
| <a name="output_regions"></a> [regions](#output\_regions) | Map of policy names to their deployed regions |
<!-- END_TF_DOCS -->