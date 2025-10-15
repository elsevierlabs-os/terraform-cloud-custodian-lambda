---
lambda_name: "${lambda_name}"
lambda_schedule: rate(10 minutes)
queue_url: https://sqs.us-east-1.amazonaws.com/${account_id}/c7n-mailer-test
role: arn:aws:iam::${account_id}:role/${lambda_name}
slack_token: xoxo-token123
region: ${region}