---
vars:
  image-age-filters: &image-age-filters
    - type: image-age
      days: 7
policies:
- name: periodic
  mode:
    type: periodic
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/policies"
      output_dir: s3://${prefix}periodic-${account_id}/output
      cache_dir: s3://${prefix}periodic-${account_id}/cache
      cache_period: 15
    schedule: rate(5 minutes)
    role: "${prefix}periodic"
    timeout: 300
    memory: 256
    tags:
      Test: 'true'
  resource: ami
  filters:
  - and: *image-age-filters