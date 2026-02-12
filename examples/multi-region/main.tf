data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  prefix     = "custodian-dev-"
}

module "cloud_custodian_s3" {
  count  = var.create_bucket ? 1 : 0
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket        = "${local.prefix}multi-region-${local.account_id}"
  force_destroy = true
}

resource "aws_iam_role" "custodian" {
  name               = "${local.prefix}multi-region-lambda"
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
    for_each = var.create_bucket ? ["${module.cloud_custodian_s3[0].s3_bucket_arn}/*"] : []
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
      "ec2:DescribeImages"
    ]

    resources = ["*"]
  }
}

module "cloud_custodian_lambda" {
  source = "../../"

  regions = var.regions

  execution_options = var.create_bucket ? {
    # Not really required but if you run custodian run you need to specify -s/--output-dir you'd then have execution-options
    # as part of the config.json with the output_dir that was specified
    "output_dir" = "s3://${local.prefix}multi-region-${local.account_id}/output"
  } : {}

  policies = templatefile("${path.module}/templates/policy.yaml.tpl", {
    prefix        = local.prefix
    account_id    = local.account_id
    create_bucket = var.create_bucket
  })

  depends_on = [
    module.cloud_custodian_s3,
    aws_iam_role.custodian
  ]
}
