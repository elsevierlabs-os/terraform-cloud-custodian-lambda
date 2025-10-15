locals {
  policies_obj  = can(jsondecode(var.policies)) ? jsondecode(var.policies) : yamldecode(var.policies)
  policies_json = can(jsondecode(var.policies)) ? var.policies : jsonencode(yamldecode(var.policies))
  policy_name   = var.policy_name != "" ? var.policy_name : local.policies_obj.policies[0].name
  policy_obj = one([
    for p in local.policies_obj.policies : p if p.name == local.policy_name
  ])
  function_prefix  = try(local.policy_obj.mode["function-prefix"], "custodian-")
  function_name    = "${local.function_prefix}${local.policy_obj.name}"
  description      = "cloud-custodian lambda policy"
  handler          = try(local.policy_obj.mode.handler, "custodian_policy.run")
  layers           = try(local.policy_obj.mode.layers, [])
  filename         = data.external.package_lambda.result["zip_path"]
  source_code_hash = data.external.package_lambda.result["sha256_base64"]
  concurrency      = try(local.policy_obj.mode.concurrency, -1)
  role_input       = try(local.policy_obj.mode.role, null)
  role = local.role_input != null ? (
    startswith(local.role_input, "arn:") ? local.role_input : data.aws_iam_role.custodian_role[0].arn
  ) : null
  runtime                = try(local.policy_obj.mode.runtime, "python3.11")
  timeout                = try(local.policy_obj.mode.timeout, 900)
  memory_size            = try(local.policy_obj.mode.memory, 512)
  subnets                = try(local.policy_obj.mode.subnets, null)
  security_groups        = try(local.policy_obj.mode.security_groups, null)
  dead_letter_config     = try(local.policy_obj.mode.dead_letter_config, null)
  dead_letter_target_arn = local.dead_letter_config != null ? try(local.dead_letter_config.TargetArn, null) : null
  environment            = try(local.policy_obj.mode.environment, null)
  environment_variables  = local.environment != null ? try(local.environment.Variables, {}) : {}
  kms_key_arn            = try(local.policy_obj.mode.kms_key_arn, null)
  tracing_config         = try(local.policy_obj.mode.tracing_config, null)
  tracing_config_mode    = local.tracing_config != null ? try(local.tracing_config.Mode, "PassThrough") : "PassThrough"
  custodian_tags         = jsondecode(data.external.package_lambda.result.custodian_tags)
  regions                = length(var.regions) > 0 ? var.regions : jsondecode(data.external.package_lambda.result.policy_regions)

  mode_type = try(local.policy_obj.mode.type, null)

  schedule = try(local.policy_obj.mode.schedule, null)
  periodic = local.mode_type == "periodic" && local.schedule != null && local.schedule != ""

  cloudwatch_event = contains([
    "cloudtrail",
    "guard-duty",
    "ec2-instance-state",
    "asg-instance-state",
    "phd",
    "hub-finding",
  ], local.mode_type)

  cloudwatch_event_pattern = local.cloudwatch_event ? try(
    data.external.cloudwatch_event[0].result["event_pattern"],
    null
  ) : null

  config_rule = contains([
    "config-rule",
    "config-poll-rule"
  ], local.mode_type)

  config_rule_params = local.config_rule ? try(
    data.external.config_rule[0].result,
    null
  ) : null
}

data "external" "validate_policy" {
  program = ["python3", "${path.module}/ops/validate_lambda_policy.py"]
  query = {
    policies    = var.policies
    policy_name = var.policy_name
  }
}

data "aws_iam_role" "custodian_role" {
  count = local.role_input != null && !startswith(local.role_input, "arn:") ? 1 : 0
  name  = local.role_input
}

data "external" "package_lambda" {
  program = ["python3", "${path.module}/ops/package_lambda_policy.py"]
  query = {
    policies          = var.policies
    policy_name       = var.policy_name
    execution_options = jsonencode(var.execution_options)
    function_name     = local.function_name
    role              = local.role
    valid             = data.external.validate_policy.result.valid
    force_deploy      = tostring(var.force_deploy)
  }
}

resource "aws_lambda_function" "custodian" {
  for_each = toset(local.regions)
  region   = each.key

  function_name                  = local.function_name
  description                    = local.description
  role                           = local.role
  handler                        = local.handler
  memory_size                    = local.memory_size
  reserved_concurrent_executions = local.concurrency
  timeout                        = local.timeout
  runtime                        = local.runtime
  layers                         = local.layers
  filename                       = local.filename
  source_code_hash               = local.source_code_hash
  publish                        = true
  architectures                  = [var.architecture]
  kms_key_arn                    = local.kms_key_arn
  tags                           = local.custodian_tags

  dynamic "vpc_config" {
    for_each = local.subnets != null && local.security_groups != null ? [true] : []
    content {
      security_group_ids = local.security_groups
      subnet_ids         = local.subnets
    }
  }

  dynamic "environment" {
    for_each = length(local.environment_variables) > 0 ? [true] : []
    content {
      variables = local.environment_variables
    }
  }

  dynamic "tracing_config" {
    for_each = local.tracing_config_mode == null ? [] : [true]
    content {
      mode = local.tracing_config_mode
    }
  }

  dynamic "dead_letter_config" {
    for_each = local.dead_letter_target_arn != null ? [true] : []
    content {
      target_arn = local.dead_letter_target_arn
    }
  }
}

resource "aws_cloudwatch_event_rule" "periodic" {
  for_each = local.periodic ? toset(local.regions) : []
  region   = each.key

  name                = local.function_name
  description         = local.description
  schedule_expression = local.schedule

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_cloudwatch_event_target" "periodic" {
  for_each = local.periodic ? toset(local.regions) : []
  region   = each.key

  rule = aws_cloudwatch_event_rule.periodic[each.key].name
  arn  = aws_lambda_function.custodian[each.key].arn

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lambda_permission" "periodic" {
  for_each = local.periodic ? toset(local.regions) : []
  region   = each.key

  statement_id  = local.function_name
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.custodian[each.key].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.periodic[each.key].arn

  lifecycle {
    create_before_destroy = true
  }
}

data "external" "cloudwatch_event" {
  count = local.cloudwatch_event ? 1 : 0
  program = [
    "python3",
    "${path.module}/ops/get_cloudwatch_event_pattern.py"
  ]
  query = {
    policies    = var.policies
    policy_name = var.policy_name
    valid       = data.external.validate_policy.result.valid
  }
}

resource "aws_cloudwatch_event_rule" "cloudwatch_event" {
  for_each = local.cloudwatch_event ? toset(local.regions) : []
  region   = each.key

  name          = local.function_name
  description   = local.description
  event_pattern = local.cloudwatch_event_pattern

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_cloudwatch_event_target" "cloudwatch_event" {
  for_each = local.cloudwatch_event ? toset(local.regions) : []
  region   = each.key

  rule = aws_cloudwatch_event_rule.cloudwatch_event[each.key].name
  arn  = aws_lambda_function.custodian[each.key].arn

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lambda_permission" "cloudwatch_event" {
  for_each = local.cloudwatch_event ? toset(local.regions) : []
  region   = each.key

  statement_id  = local.function_name
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.custodian[each.key].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cloudwatch_event[each.key].arn

  lifecycle {
    create_before_destroy = true
  }
}

data "external" "config_rule" {
  count = local.config_rule ? 1 : 0
  program = [
    "python3",
    "${path.module}/ops/get_config_rule_params.py"
  ]
  query = {
    policies = var.policies
    valid    = data.external.validate_policy.result.valid
  }
}

resource "aws_config_config_rule" "config_rule" {
  for_each = local.config_rule ? toset(local.regions) : []
  region   = each.key

  name        = local.config_rule_params["ConfigRuleName"]
  description = local.config_rule_params["Description"]

  dynamic "scope" {
    for_each = local.config_rule_params["Scope"] != null ? [1] : []
    content {
      compliance_resource_types = jsondecode(local.config_rule_params["Scope"])["ComplianceResourceTypes"]
    }
  }

  source {
    owner             = jsondecode(local.config_rule_params["Source"])["Owner"]
    source_identifier = aws_lambda_function.custodian[each.key].arn
    source_detail {
      event_source = jsondecode(local.config_rule_params["Source"])["SourceDetails"][0]["EventSource"]
      message_type = jsondecode(local.config_rule_params["Source"])["SourceDetails"][0]["MessageType"]
    }
  }

  maximum_execution_frequency = contains(keys(local.config_rule_params), "MaximumExecutionFrequency") ? local.config_rule_params["MaximumExecutionFrequency"] : null

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lambda_permission" "config_rule" {
  for_each = local.config_rule ? toset(local.regions) : []
  region   = each.key

  statement_id  = local.function_name
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.custodian[each.key].function_name
  principal     = "config.amazonaws.com"

  lifecycle {
    create_before_destroy = true
  }
}
