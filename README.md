# Ansible Role: cloudwatch-dashboards

Ansible role to create and rebuild AWS CloudWatch Dashboards in a dynamic way. The dashboards are built based on custom templates, see [example](templates/example.j2).

## Requirements

- Ansible 2.4+
- boto3

## Module

This role includes an AWS custom module. There is a [documentation in code](library/cloudwatch_dashboard.py).

## Role Variables

Available variables are listed below, along with default values (see `defaults/main.yml`):
```yaml
cloudwatch_dashboards:
  - name: My Dashboard
    template: example.j2
    describe_resources:
      ec2_instance_filter:
        "tag:Name": app_name
        instance-state-name: running
      elb:
        - elb_name
      cloudfront:
        - id: Q03I1XDOS00WEP
          label: cdn_name

## Example Playbook
- hosts: all
  vars:
    cloudwatch_dashboards:
      - name: My Dashboard
        template: example.j2
        describe_resources:
          ec2_instance_filter:
            "tag:Name": app_name

  roles:
    - role: cloudwatch-dashboards.chaordic
```

## License

GPLv3

## Author Information

Cloud Infrastructure Team, Linx Impulse
