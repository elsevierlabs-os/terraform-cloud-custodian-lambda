---
vars:
  image-age-filters: &image-age-filters
    - type: image-age
      days: 7
policies:
- name: ami-age
  mode:
    type: periodic
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/policies"
      output_dir: s3://${prefix}multi-policies-${account_id}/output
      cache_dir: s3://${prefix}multi-policies-${account_id}/cache
      cache_period: 15
    schedule: cron(0 11 ? * 3 *)
    role: "${prefix}multi-policies"
    timeout: 300
    memory: 256
    tags:
      Test: 'true'
  resource: ami
  filters:
  - and: *image-age-filters

- name: ec2-ami-age
  mode:
    type: periodic
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/policies"
      output_dir: s3://${prefix}multi-policies-${account_id}/output
      cache_dir: s3://${prefix}multi-policies-${account_id}/cache
      cache_period: 15
    schedule: cron(0 11 ? * 3 *)
    role: "${prefix}multi-policies"
    timeout: 300
    memory: 256
    tags:
      Test: 'true'
  resource: ec2
  filters:
  - and: *image-age-filters
  - "State.Name": "running"
