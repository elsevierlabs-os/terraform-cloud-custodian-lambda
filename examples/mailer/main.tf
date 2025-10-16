data "aws_caller_identity" "current" {}

locals {
  account_id  = data.aws_caller_identity.current.account_id
  lambda_name = "cloud-custodian-dev-mailer"
}

resource "aws_iam_role" "custodian" {
  name               = local.lambda_name
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

module "cloud_custodian_lambda_mailer" {
  source = "../../modules/cloud-custodian-lambda-mailer"

  mailer = templatefile("${path.module}/templates/mailer.yaml.tpl", {
    lambda_name = local.lambda_name
    account_id  = local.account_id
    region      = var.region
  })

  templates = "${path.module}/files/mailer_templates"
}
