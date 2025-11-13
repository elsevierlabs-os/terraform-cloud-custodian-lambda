---
vars:
  image-age-filters: &image-age-filters
    - type: image-age
      days: 7
policies:
- name: ami-age
  mode:
    type: schedule
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/policies"
      output_dir: s3://${prefix}multi-policies-${account_id}/output
      cache_dir: s3://${prefix}multi-policies-${account_id}/cache
      cache_period: 15
    schedule: cron(0 11 ? * 3 *)
    timezone: Europe/London
    scheduler-role: ${prefix}multi-policies-scheduler
    role: ${prefix}multi-policies-lambda
  resource: ami
  filters:
  - and: *image-age-filters

- name: ec2-ami-age
  mode:
    type: schedule
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/policies"
      output_dir: s3://${prefix}multi-policies-${account_id}/output
      cache_dir: s3://${prefix}multi-policies-${account_id}/cache
      cache_period: 15
    schedule: cron(0 11 ? * 3 *)
    timezone: Europe/London
    scheduler-role: ${prefix}multi-policies-scheduler
    role: ${prefix}multi-policies-lambda
  resource: ec2
  filters:
  - and: *image-age-filters
  - "State.Name": "running"

- name: ec2-public-ami
  mode:
    type: ec2-instance-state
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/policies"
      output_dir: s3://${prefix}multi-policies-${account_id}/output
      cache_dir: s3://${prefix}multi-policies-${account_id}/cache
      cache_period: 15
    role: "${prefix}multi-policies-lambda"
    events:
    - pending
    - running
  resource: ec2
  filters:
  - and:
    - type: image
      key: Public
      value: true
