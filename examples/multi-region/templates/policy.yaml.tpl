---
vars:
  image-age-filters: &image-age-filters
    - type: image-age
      days: 7
policies:
- name: multi-region
  mode:
    type: periodic
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/policies"
%{ if use_s3 ~}
      output_dir: s3://$${prefix}multi-region-$${account_id}/output
      cache_dir: s3://$${prefix}multi-region-$${account_id}/cache
      cache_period: 15
%{ endif ~}
    schedule: cron(0 11 ? * 3 *)
    role: "${prefix}multi-region-lambda"
    timeout: 300
    memory: 256
    tags:
      Test: 'true'
  conditions:
    - type: value
      key: region
      op: in
      value:
      - eu-west-1
      - us-east-1
      - us-east-2
  resource: ami
  filters:
  - and: *image-age-filters