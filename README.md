# Cloud custodian lambda

A collection of terraform modules that allow you to deploy and manage cloud-custodian lambda resources using native terraform as opposed to using the cloud-custodian CLI. 

This project contains:
* A terraform module to create a [cloud custodian lambda policy](https://cloudcustodian.io/docs/aws/lambda.html) across multiple regions. The user provides a single cloud-custodian policy in either YAML or JSON format and based on this associated lambda resources are created and managed by terraform. Note: The `vars` section with YAML anchors/aliases is only supported in YAML format. Located in the root of this github repository
* A terraform module to create multiple [cloud custodian lambda policies](https://cloudcustodian.io/docs/aws/lambda.html) across multiple regions. The user provides multiple policies in either YAML or JSON format and based on this associated lambda resources are created and managed by terraform. Note: The `vars` section with YAML anchors/aliases is only supported in YAML format. Using this module allows you to use the same `vars` across multiple policies. Located in [modules/cloud-custodian-lambda-mailer](./modules/cloud-custodian-lambda-policies/README.md)
* A terraform module to create [cloud custodian lambda mailer](https://cloudcustodian.io/docs/tools/c7n-mailer.html). The user provides mailer config in either YAML or JSON format and based on this associated lambda resources are created and managed by terraform. Located in [modules/cloud-custodian-lambda-mailer](./modules/cloud-custodian-lambda-mailer/README.md)

## Python Setup

The modules use python scripts where necessary to transform cloud-custodian config for use in different AWS resources. In order for this to work, you will need to have `python3`, the [cloud custodian](https://github.com/cloud-custodian/cloud-custodian) python modules and any dependencies installed. The following example uses [uv](https://docs.astral.sh/uv/) and a virtualenv, but this can be done other ways:

```sh
# From the module root which contains uv.lock, pyproject.toml etc
# Install only production dependencies (just c7n)
uv sync --frozen --no-dev

# Activate the virtual environment
source .venv/bin/activate
```

## Managing Cloud Custodian Policies

### Prerequisites

* You will need an S3 bucket to store results
* You will need an IAM role which will run the lambda, this will require permissions to post the report to the S3 bucket, create logs and metrics (if required) in cloudwatch and other permissions specific to the policy.

### Terraform

The example below deploys a single policy which finds security group rules open to port 22 in eu-west-1, us-east-1 and us-east-2:

```sh
module "cloud_custodian_lambda" {
  source = "./"

  regions = [
    "eu-west-1",
    "us-east-1",
    "us-east-2"
  ]

  execution_options = {
    # Not really required but if you run custodian run you need to specify -s/--output-dir you'd then have execution-options
    # as part of the config.json with the output_dir that was specified
    "output_dir" = "s3://<your-custodian-bucket>/outputregion=<region>"
  }
  policies = <<EOF
---
policies:
- name: cloudtrail
  mode:
    type: cloudtrail
    function-prefix: custodian-
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: /cloud-custodian/policies
      output_dir: s3://<your-custodian-bucket>/output
    role: arn:aws:iam:::role/<your-iam-role>
    events:
    - source: ec2.amazonaws.com
      event: AuthorizeSecurityGroupIngress
      ids: responseElements.securityGroupRuleSet.items[].groupId
    - source: ec2.amazonaws.com
      event: RevokeSecurityGroupIngress
      ids: requestParameters.groupId
  resource: security-group
  filters:
  - and:
    - type: ingress
      Ports:
      - 22
      Cidr:
        value_type: cidr
        op: in
        value:
        - 0.0.0.0/0
EOF
}
```

There are [examples](./examples) for different policies as well as for using [custodian mailer](https://cloudcustodian.io/docs/tools/c7n-mailer.html). If your input was JSON then you can get a pretty printed YAML of the policies and output to a file with the following:

```sh
terraform output -raw policies_yaml | python3 -c 'import sys, yaml; yaml.Dumper.ignore_aliases = lambda *args: True; print(yaml.safe_dump(yaml.safe_load(sys.stdin), default_flow_style=False))' > policies.yaml
```

After this is done you can use the usual cloud custodian commands such as `custodian report -s s3://<bucket> policies.yaml` to get the results of the policies after they have been run.

### Advanced Usage

* [Multiple regions](./docs/MULTIPLE_REGIONS.md)
* [Multiple policies](./modules/cloud-custodian-lambda-policies/README.md)

### Troubleshooting

See [Troubleshooting](./docs/TROUBLESHOOTING.md)

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
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.11.0 |
| <a name="provider_external"></a> [external](#provider\_external) | 2.3.5 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_event_rule.cloudwatch_event](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_rule.periodic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target.cloudwatch_event](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_cloudwatch_event_target.periodic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_config_config_rule.config_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/config_config_rule) | resource |
| [aws_lambda_function.custodian](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_permission.cloudwatch_event](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.config_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.periodic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_iam_role.custodian_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_role) | data source |
| [external_external.cloudwatch_event](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |
| [external_external.config_rule](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |
| [external_external.package_lambda](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |
| [external_external.validate_policy](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_policies"></a> [policies](#input\_policies) | Policies in JSON or YAML format, this should either contain one policy or if it contains multiple `policy_name` should be provided.<br/>    Note: The 'vars' section with YAML anchors/aliases is only supported in YAML format. | `string` | n/a | yes |
| <a name="input_architecture"></a> [architecture](#input\_architecture) | Architecture for the Lambda function. Allowed: arm64 or x86\_64. | `string` | `"arm64"` | no |
| <a name="input_execution_options"></a> [execution\_options](#input\_execution\_options) | Execution options for the AWS Lambda function.<br/>    Note that these are execution-options that would be set via the CLI when running `custodian run`.<br/>    You can also set a more wide range of execution-options within the policy.<br/>    See: https://cloudcustodian.io/docs/aws/lambda.html#execution-options | `map(any)` | `{}` | no |
| <a name="input_force_deploy"></a> [force\_deploy](#input\_force\_deploy) | Force redeployment of Lambda functions by updating a deployment timestamp tag.<br/>    Set to true to trigger redeployment when source\_code\_hash doesn't detect changes. | `bool` | `false` | no |
| <a name="input_policy_name"></a> [policy\_name](#input\_policy\_name) | Optional: Extract a specific policy by name from multi-policy YAML. If not provided, expects single policy YAML. | `string` | `""` | no |
| <a name="input_regions"></a> [regions](#input\_regions) | Regions to deploy the policy to | `list(string)` | <pre>[<br/>  "us-east-1"<br/>]</pre> | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cloudwatch_event_pattern"></a> [cloudwatch\_event\_pattern](#output\_cloudwatch\_event\_pattern) | The event pattern for event mode |
| <a name="output_cloudwatch_event_rule"></a> [cloudwatch\_event\_rule](#output\_cloudwatch\_event\_rule) | Complete AWS Cloudwatch Event Rule for cloudwatch event resource with all attributes |
| <a name="output_cloudwatch_event_rule_arn"></a> [cloudwatch\_event\_rule\_arn](#output\_cloudwatch\_event\_rule\_arn) | The ARN of the CloudWatch Event Rule for event mode |
| <a name="output_cloudwatch_event_rule_name"></a> [cloudwatch\_event\_rule\_name](#output\_cloudwatch\_event\_rule\_name) | The name of the CloudWatch Event Rule for event mode |
| <a name="output_config_rule"></a> [config\_rule](#output\_config\_rule) | Complete AWS Config Rule resource with all attributes |
| <a name="output_config_rule_arn"></a> [config\_rule\_arn](#output\_config\_rule\_arn) | The ARN of the AWS Config Rule |
| <a name="output_config_rule_name"></a> [config\_rule\_name](#output\_config\_rule\_name) | The name of the AWS Config Rule |
| <a name="output_config_rule_rule_id"></a> [config\_rule\_rule\_id](#output\_config\_rule\_rule\_id) | The ID of the AWS Config Rule |
| <a name="output_lambda_function"></a> [lambda\_function](#output\_lambda\_function) | Complete AWS Lambda function resource with all attributes |
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | Map of Lambda function ARNs by region |
| <a name="output_lambda_function_filename"></a> [lambda\_function\_filename](#output\_lambda\_function\_filename) | Map of Lambda function filenames by region |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | Map of Lambda function names by region |
| <a name="output_lambda_function_role"></a> [lambda\_function\_role](#output\_lambda\_function\_role) | Map of Lambda function IAM roles by region |
| <a name="output_lambda_function_source_code_hash"></a> [lambda\_function\_source\_code\_hash](#output\_lambda\_function\_source\_code\_hash) | Map of Lambda function source code hashes by region |
| <a name="output_lambda_function_source_code_size"></a> [lambda\_function\_source\_code\_size](#output\_lambda\_function\_source\_code\_size) | Map of Lambda function source code sizes by region |
| <a name="output_lambda_function_tags"></a> [lambda\_function\_tags](#output\_lambda\_function\_tags) | Map of Lambda function tags by region |
| <a name="output_mode_type"></a> [mode\_type](#output\_mode\_type) | The type of Cloud Custodian mode (periodic, cloudtrail, config-rule, etc.) |
| <a name="output_package_lambda_result"></a> [package\_lambda\_result](#output\_package\_lambda\_result) | Full output from package lambda step |
| <a name="output_package_versions"></a> [package\_versions](#output\_package\_versions) | JSON string containing versions of all packages included in the Lambda deployment |
| <a name="output_periodic_event_rule"></a> [periodic\_event\_rule](#output\_periodic\_event\_rule) | Complete AWS Cloudwatch Event Rule for periodic resource with all attributes |
| <a name="output_periodic_event_rule_arn"></a> [periodic\_event\_rule\_arn](#output\_periodic\_event\_rule\_arn) | The ARN of the CloudWatch Event Rule for periodic mode |
| <a name="output_periodic_event_rule_name"></a> [periodic\_event\_rule\_name](#output\_periodic\_event\_rule\_name) | The name of the CloudWatch Event Rule for periodic mode |
| <a name="output_periodic_schedule_expression"></a> [periodic\_schedule\_expression](#output\_periodic\_schedule\_expression) | The schedule expression for periodic mode |
| <a name="output_policies_json"></a> [policies\_json](#output\_policies\_json) | The policies rendered as JSON (only the specific policy if policy\_name is set) |
| <a name="output_policies_yaml"></a> [policies\_yaml](#output\_policies\_yaml) | The policies rendered as YAML (only the specific policy if policy\_name is set) |
| <a name="output_policy_name"></a> [policy\_name](#output\_policy\_name) | The name of the policy being deployed (if policy\_name was specified) |
| <a name="output_regions"></a> [regions](#output\_regions) | Regions that the policy is deployed to |
| <a name="output_sha256_hex"></a> [sha256\_hex](#output\_sha256\_hex) | SHA256 hash of the Lambda package in hexadecimal format |
<!-- END_TF_DOCS -->