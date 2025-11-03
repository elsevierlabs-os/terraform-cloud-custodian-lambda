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
      log_group: "/cloud-custodian/policies"
      output_dir: s3://${prefix}schedule-${account_id}/output
      cache_dir: s3://${prefix}schedule-${account_id}/cache
      cache_period: 15
    schedule: rate(5 minutes)
    timezone: Europe/London
    group-name: ${prefix}schedule-group
    scheduler-role: arn:aws:iam::${account_id}:role/${prefix}scheduler
    role: "${prefix}schedule"
  resource: ami
  filters:
  - and: *image-age-filters
