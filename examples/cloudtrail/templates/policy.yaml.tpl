---
policies:
- name: cloudtrail
  mode:
    type: cloudtrail
    function-prefix: "${prefix}"
    execution-options:
      metrics_enabled: true
      dryrun: false
      log_group: "/cloud-custodian/policies"
%{ if use_s3 ~}
      output_dir: s3://$${prefix}cloudtrail-$${account_id}/output
      cache_dir: s3://$${prefix}cloudtrail-$${account_id}/cache
      cache_period: 15
%{ endif ~}
    role: arn:aws:iam::${account_id}:role/${prefix}cloudtrail-lambda
    events:
    - source: ec2.amazonaws.com
      event: AuthorizeSecurityGroupIngress
      ids: responseElements.securityGroupRuleSet.items[].groupId
    - source: ec2.amazonaws.com
      event: RevokeSecurityGroupIngress
      ids: requestParameters.groupId
  resource: security-group
  filters:
  - and:
    - type: ingress
      Ports:
      - 22
      Cidr:
        value_type: cidr
        op: in
        value:
        - 0.0.0.0/0