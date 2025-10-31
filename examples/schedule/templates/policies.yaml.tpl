---
vars:
  image-age-filters: &image-age-filters
    - type: image-age
      days: 7
policies:
- name: schedule
  mode:
    type: schedule
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/${account_id}/"
      output_dir: s3://${prefix}schedule-${account_id}/output
      cache_dir: s3://${prefix}schedule-${account_id}/cache
      cache_period: 15
    schedule: cron(0 11 ? * 3 *)
    timezone: Europe/London
    group-name: ${schedule_group}
    scheduler-role: ${scheduler_role_arn}
    role: "${prefix}schedule"
    timeout: 300
    memory: 256
    tags:
      Test: 'true'
  resource: ami
  filters:
  - and: *image-age-filters
