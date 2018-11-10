# Ansible Role: cloudwatch-dashboards

Ansible role to create and rebuild AWS CloudWatch Dashboards in a dynamic way. The dashboards are built based on custom templates, see [example](https://github.com/chaordic/ansible-role-cloudwatch-dashboards/blob/master/meta/main.yml).

## Requirements

- Ansible 2.4+
- boto3

## Module

This role includes an AWS custom module. There is a [documentation in code](.....library/cloudwatch_dashboard.py).

## Role Variables

Available variables are listed below, along with default values (see `defaults/main.yml`):
```yaml
cloudwatch_dashboards:
  - name: My Frontend Dashboard
    template: example.j2
    elb_name: elb-frontend
    ec2_tag_field: Name
    ec2_tag_value: my-frontend-app-name

  - name: My Backend Dashboard
    template: example.j2
    elb_name: elb-backend
    ec2_tag_field: Name
    ec2_tag_value: my-backend-app-name
```

## Example Playbook
```yaml
- hosts: all
  vars:
    cloudwatch_dashboards:
      - name: My Dashboard
        template: example.j2
        elb_name: my-elb-app
        ec2_tag_field: Name
        ec2_tag_value: my-app-name

  roles:
    - role: cloudwatch-dashboards.chaordic
```

## License

GPLv3

## Author Information

Cloud Infrastructure Team, Linx Impulse
