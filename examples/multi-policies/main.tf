data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  prefix     = "custodian-dev-"
}

module "cloud_custodian_s3" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket        = "${local.prefix}multi-policies-${local.account_id}"
  force_destroy = true
}

resource "aws_iam_role" "custodian" {
  name               = "${local.prefix}multi-policies"
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
      "ec2:DescribeImages",
      "ec2:DescribeInstances"
    ]

    resources = ["*"]
  }
}

module "custodian_policies" {
  source = "../../modules/cloud-custodian-lambda-policies"

  policies = templatefile("${path.module}/templates/policies.yaml.tpl", {
    prefix     = local.prefix
    account_id = local.account_id
  })
  regions = var.regions

  depends_on = [
    module.cloud_custodian_s3,
    aws_iam_role.custodian
  ]
}
