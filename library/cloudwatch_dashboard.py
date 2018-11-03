#!/usr/bin/python

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '0.1'}

DOCUMENTATION = '''
---
module: cloudwatch_dashboard
short_description: Manage AWS CloudWatch Dashboards
description:
    - Manage AWS CloudWatch Dashboards
requirements: ['boto3', 'botocore']
author: "Raphael Pereira Ribeiro (@raphapr)"
options:
  name:
    description:
      - The name of the dashboard
    required: true
  state:
    description:
      - Attribute that specifies if the dashboard has to be created or deleted.
    required: false
    default: present
    choices: ['present', 'absent']
  widgets:
    description:
      - A list of widgets to add to the dashboard; fields allowed are - name (str; required), type (str; 'metric'),
        x (int), y (int), height (int; 6), width (int; 6), view (str), stacked (bool; False), metrics (list), period (int, 300),
        stat (str), yaxis_left ([min,max]; [0,100]), yaxis_right ([min,max], [0,100]), annotations (raw), markdown (str).
        Reference: https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/CloudWatch-Dashboard-Body-Structure.html
    required: true
'''

EXAMPLES = '''
---
- name: Create cloudwatch dashboard widgets
  cloudwatch_dashboard:
    name: MyDashboard
    state: present
    widgets:
    - name: "CPU Utilization"
      type: metric
      x: 6
      y: 6
      height: 6
      width: 6
      view: timeSeries
      stacked: False
      metrics:
          - [ "AWS/EC2", "CPUUtilization", "InstanceId", "i-09axa656b033v0f1a", { "period": 60, "label": "my ec2 instance" } ]
      period: 300
      stat: Sum
      yaxis_left: [0, 3000]
      yaxis_right: [0, 27800]
    - name: "Text widget"
      type: text
      markdown: "This is markdown, bitch!"
'''

RETURN = '''
'''


try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import json
import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, ec2_argument_spec,
                                      get_aws_connection_info, camel_dict_to_snake_dict)

from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

class CWDashboard:

    def __init__(self, module, client, name, state, widgets):

        self.module = module
        self.client = client
        self.state = state
        self.name = name
        self.widgets = widgets

        for w in widgets:
            if 'type' not in w:
                w['type'] = 'metric'

            if not (w['type'] == 'metric' or w['type'] == 'text'):
                module.fail_json(msg="value of type for widget %s must be one "
                                     "of: metric,text, got: %s"
                                     % (w['name'], w['type']))

            if w['type'] == 'text':
                if 'markdown' not in w:
                    module.fail_json(msg="markdown must be set for "
                                     "widget %s when metric type is text"
                                     % w['name'])

            if w['type'] == 'metric' and 'metrics' not in w:
                module.fail_json(msg="metrics must be set for widget %s"
                                 % w['name'])

            if 'region' not in w:
                w['region'] = 'us-east-1'

        self.result = {
            'changed': False,
            'name': self.name,
            'state': self.state,
            'diff': {
                'before': {},
                'after': {}
            }
        }

    def create_widgets(self):

        widgets = []

        for w in self.widgets:

            if w['type'] == 'metric':

                widget_aux = {'type': w['type'],
                              'properties': {'metrics': w['metrics'],
                                             'title': w['name'],
                                             'region': w['region']}}

                if 'view' in w:
                    widget_aux['properties']['view'] = w['view']

                if 'stacked' in w:
                    widget_aux['properties']['stacked'] = w['stacked']

                if 'period' in w:
                    widget_aux['properties']['period'] = w['period']

                if 'stat' in w:
                    widget_aux['properties']['stat'] = w['stat']

                if 'yaxis_left' or 'yaxis_right' in w:
                    widget_aux['properties']['yAxis'] = {}

                if 'yaxis_left' in w:
                    widget_aux['properties']['yAxis']['left'] = {'min': w['yaxis_left'][0],
                                                                 'max': w['yaxis_left'][1]}

                if 'yaxis_right' in w:
                    widget_aux['properties']['yAxis']['right'] = {'min': w['yaxis_right'][0],
                                                                  'max': w['yaxis_right'][1]}

                if 'annotations' in w:
                    widget_aux['properties']['annotations'] = self.annotations

            elif w['type'] == 'text':
                widget_aux = {'type': w['type'],
                              'properties': {'markdown': w['markdown']}}

            if 'x' in w:
                widget_aux['x'] = w['x']

            if 'y' in w:
                widget_aux['y'] = w['y']

            if 'height' in w:
                widget_aux['height'] = w['height']

            if 'width' in w:
                widget_aux['width'] = w['width']

            widgets.append(widget_aux)

        body = {'widgets': widgets}
        body_j = json.dumps(body)

        try:
            current_body = self.client.get_dashboard(DashboardName=self.name)

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "ResourceNotFound":
                pass
        except (botocore.exceptions.BotoCoreError,
                botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e,
                                      msg="Couldn't get current dashboard %s"
                                      % self.name)

        try:
            current_body
            current_body = current_body['DashboardBody']
            self.result['changed'] = self.compare_dashboard_body(body_j,
                                                             current_body)
        except NameError:
            pass

        if self.module.check_mode:
            response = {'msg': 'There is no http response in check mode.'}
        else:
            try:
                response = self.client.put_dashboard(DashboardName=self.name,
                                                     DashboardBody=body_j)
            except (botocore.exceptions.BotoCoreError,
                    botocore.exceptions.ClientError) as e:
                self.module.fail_json_aws(e, msg="Couldn't put dashboard %s"
                                          % self.name)

        self.result['response'] = response

    def compare_dashboard_body(self, user_body, current_body):
        return user_body != current_body


    def get_result(self):
        return self.result


def get_cw_client(module):
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module,
                                                                  boto3=HAS_BOTO3)
    if not region:
            module.fail_json(msg="The AWS region must be specified as an "
                                 "environment variable or in the AWS "
                                 "credentials profile.")
    try:
        client = boto3_conn(module,
                            conn_type='client',
                            resource='cloudwatch',
                            region=region,
                            endpoint=ec2_url,
                            **aws_connect_kwargs)
        return client
    except (botocore.exceptions.ClientError,
            botocore.exceptions.ValidationError) as e:
        module.fail_json_aws(e, msg="Failure connecting boto3 to AWS: %s"
                             % to_native(e), exception=traceback.format_exc())


def main():

    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(choices=['absent', 'present'], default='present'),
        widgets=dict(type='list', required=True)
    )

    module = AnsibleAWSModule(
            argument_spec=module_args,
            supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']
    widgets = module.params['widgets']

    cww = CWDashboard(module,
                      get_cw_client(module),
                      name,
                      state,
                      widgets)

    if state == "present":
        cww.create_widgets()

    result = cww.get_result()
    module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
