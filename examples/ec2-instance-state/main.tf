data "aws_caller_identity" "current" {}

locals {
  region     = "eu-west-1"
  account_id = data.aws_caller_identity.current.account_id
  prefix     = "custodian-dev-"
}

module "cloud_custodian_s3" {
  count  = var.create_ec2_instance_state_s3_bucket ? 1 : 0
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket        = "${local.prefix}ec2-instance-state-${local.account_id}"
  force_destroy = true
}

resource "aws_iam_role" "custodian" {
  name               = "${local.prefix}ec2-instance-state-lambda"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "custodian" {
  role = aws_iam_role.custodian.id

  policy = data.aws_iam_policy_document.custodian.json
}

data "aws_iam_policy_document" "custodian" {
  dynamic "statement" {
    for_each = var.create_ec2_instance_state_s3_bucket ? ["${module.cloud_custodian_s3[0].s3_bucket_arn}/*"] : []
    content {
      actions = [
        "s3:PutObject",
      ]

      resources = [
        statement.value
      ]
    }
  }

  statement {

    actions = [
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:CreateLogStream",
      "logs:CreateLogGroup",
      "cloudwatch:PutMetricData",
    ]

    resources = ["*"]
  }

  statement {

    actions = [
      "ec2:DescribeInstances"
    ]

    resources = ["*"]
  }
}

module "cloud_custodian_lambda" {
  source = "../../"

  regions = [local.region]

  execution_options = var.create_ec2_instance_state_s3_bucket ? {
    # Not really required but if you run custodian run you need to specify -s/--output-dir you'd then have execution-options
    # as part of the config.json with the output_dir that was specified
    "output_dir" = "s3://${local.prefix}ec2-instance-state-${local.account_id}/output?region=${local.region}"
  } : {}

  force_deploy = var.force_deploy

  policies = <<EOF
{
  "policies": [
    {
      "name": "ec2-instance-state",
      "mode": {
        "type": "ec2-instance-state",
        "function-prefix": "${local.prefix}",
        "execution-options": ${jsonencode(merge(
          {
            metrics_enabled = true
            dryrun = false
            log_group = "/cloud-custodian/policies"
          },
          var.create_ec2_instance_state_s3_bucket ? {
            output_dir = "s3://${local.prefix}ec2-instance-state-${local.account_id}/output"
            cache_dir = "s3://${local.prefix}ec2-instance-state-${local.account_id}/cache"
            cache_period = 15
          } : {}
        ))},
        "role": "arn:aws:iam::${local.account_id}:role/${local.prefix}ec2-instance-state-lambda",
        "events": [
          "terminated"
        ]
      },
      "resource": "ec2"
    }
  ]
}
EOF

  depends_on = [
    module.cloud_custodian_s3,
    aws_iam_role.custodian
  ]
}
