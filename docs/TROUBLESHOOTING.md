# Troubleshooting

## aws_lambda_function does not detect source code drift

To get around https://github.com/hashicorp/terraform-provider-aws/issues/41092 you should ensure you are outputting `output.lambda_function` and check if `code_sha256` is changing. If it is then set the `var.force_apply` to true and re-run terraform, this will add a `force-deploy` tag to the config.json within the lambda under `mode.tags` and also add the tag to the lambda itself. The tag value will be a timestamp of the apply. This will force the `source_code_hash` to change, which will mean the lambda function will redeploy with the updated source code. When run without this tag the `force-deploy` tag will not be present.