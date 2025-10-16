data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  prefix     = "custodian-dev-"
}

module "cloud_custodian_s3" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket        = "${local.prefix}multi-region-${local.account_id}"
  force_destroy = true
}

resource "aws_iam_role" "custodian" {
  name               = "${local.prefix}multi-region"
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
  statement {

    actions = [
      "s3:PutObject",
    ]

    resources = [
      "${module.cloud_custodian_s3.s3_bucket_arn}/*",
    ]
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

  policies = templatefile("${path.module}/templates/policy.yaml.tpl", {
    prefix     = local.prefix
    account_id = local.account_id
  })

  depends_on = [
    module.cloud_custodian_s3,
    aws_iam_role.custodian
  ]
}
