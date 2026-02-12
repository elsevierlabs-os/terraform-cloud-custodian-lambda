locals {
  mailer_json      = can(jsondecode(var.mailer)) ? var.mailer : jsonencode(yamldecode(var.mailer))
  mailer_config    = try(data.external.validate_mailer.result.mailer_config, "{}")
  mailer_obj       = try(jsondecode(local.mailer_config), {})
  lambda_name      = try(local.mailer_obj.lambda_name, "cloud-custodian-mailer")
  description      = try(local.mailer_obj.lambda_description, "Cloud Custodian Mailer")
  handler          = "periodic.dispatch"
  filename         = data.external.package_lambda.result["zip_path"]
  source_code_hash = data.external.package_lambda.result["sha256_base64"]
  runtime          = try(local.mailer_obj.runtime, "python3.11")
  memory_size      = try(local.mailer_obj.memory, 1024)
  timeout          = try(local.mailer_obj.timeout, 300)
  role_input       = try(local.mailer_obj.role, null)
  role = local.role_input != null ? (
    startswith(local.role_input, "arn:") ? local.role_input : data.aws_iam_role.custodian_role[0].arn
  ) : null
  subnets                = try(local.mailer_obj.subnets, null)
  security_groups        = try(local.mailer_obj.security_groups, null)
  dead_letter_config     = try(local.mailer_obj.dead_letter_config, null)
  dead_letter_target_arn = local.dead_letter_config != null ? try(local.dead_letter_config.TargetArn, null) : null
  region                 = try(local.mailer_obj.region, "us-east-1")
  schedule               = try(local.mailer_obj.lambda_schedule, "rate(5 minutes)")
  custodian_tags         = jsondecode(data.external.package_lambda.result.custodian_tags)
}

data "external" "validate_mailer" {
  program = ["python3", "${path.module}/../../ops/validate_lambda_mailer.py"]
  query = {
    mailer    = var.mailer
    templates = var.templates
  }
}

data "aws_iam_role" "custodian_role" {
  count = try(!startswith(local.role_input, "arn:"), false) ? 1 : 0
  name  = local.role_input
}

data "external" "package_lambda" {
  program = ["python3", "${path.module}/../../ops/package_lambda_mailer.py"]
  query = {
    mailer_config = local.mailer_config
    lambda_name   = local.lambda_name
    force_deploy  = tostring(var.force_deploy)
  }
}

resource "aws_lambda_function" "custodian" {
  region           = local.region
  filename         = local.filename
  function_name    = local.lambda_name
  description      = local.description
  role             = local.role
  handler          = local.handler
  source_code_hash = local.source_code_hash
  runtime          = local.runtime
  publish          = true
  architectures    = [var.architecture]
  memory_size      = local.memory_size
  timeout          = local.timeout
  tags             = local.custodian_tags

  dynamic "vpc_config" {
    for_each = local.subnets != null && local.security_groups != null ? [true] : []
    content {
      security_group_ids = local.security_groups
      subnet_ids         = local.subnets
    }
  }

  dynamic "dead_letter_config" {
    for_each = local.dead_letter_target_arn == null ? [] : [true]
    content {
      target_arn = local.dead_letter_target_arn
    }
  }
}

resource "aws_cloudwatch_event_rule" "custodian" {
  region = local.region

  name                = aws_lambda_function.custodian.function_name
  description         = local.description
  schedule_expression = local.schedule

  lifecycle {
    create_before_destroy = true
  }

}

resource "aws_cloudwatch_event_target" "custodian" {
  region = local.region

  rule = aws_cloudwatch_event_rule.custodian.name
  arn  = aws_lambda_function.custodian.arn

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lambda_permission" "custodian" {
  region = local.region

  statement_id  = aws_lambda_function.custodian.function_name
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.custodian.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.custodian.arn

  lifecycle {
    create_before_destroy = true
  }
}
