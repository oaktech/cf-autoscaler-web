from __future__ import print_function

import json
import os
from os import path
import yaml

org_name = None
space_name = None
autoscaler_api_url = None
secret = None
token = None
app_id = None
space_id = None
space = None
org = None
validate_ssl = True
scaling_monitor_interval = 5
scaling_min_instances = 1
scaling_max_instances = 50
scaling_memory = [
    128,
    192,
    256,
    384,
    512,
    768,
    1024,
    2048,
    3072,
    4096,
    5120,
    6144,
    7168,
    8192,
    9216,
    10240,
]
scaling_disk = [
    128,
    192,
    256,
    384,
    512,
    768,
    1024,
    2048,
    3072,
    4096,
    5120,
    6144,
    7168,
    8192,
    9216,
    10240,
]


def _parse_bool(val):
    if isinstance(val, bool):
        return val
    else:
        val = val.lower().strip()
        if val == 'false':
            return False
        else:
            return True


def get_scaling_num_instances(app=None):
    scaling = dict(
        min_num_instances=scaling_min_instances,
        max_num_instances=scaling_max_instances,
    )
    if not app:
        return scaling

    if app.scaling_config and len(app.scaling_config) > 0:
        scaling['min_num_instances'] = \
            max(int(app.scaling_config.get('min_num_instances', 1)),
                scaling_min_instances)
        scaling['max_num_instances'] = \
            min(int(app.scaling_config.get('max_num_instances', 500)),
                scaling_max_instances)
    return scaling


def get_config_vcap_application():
    global app_id
    global space_id

    if 'VCAP_APPLICATION' in os.environ and os.environ['VCAP_APPLICATION']:
        try:
            vcap_application = json.loads(os.environ['VCAP_APPLICATION'])
            space_id = vcap_application['space_id']
            app_id = vcap_application['application_id']

        except BaseException as e:
            print ('Unable to parse VCAP_APPLICATION')
            raise e


def get_env_config():
    global org_name
    global space_name
    global validate_ssl
    global secret
    global token
    global app_id
    global space_id
    global autoscaler_api_url
    global scaling_monitor_interval
    global scaling_min_instances
    global scaling_max_instances

    autoscaler_api_url = os.environ['CFAS_API_URL']
    token = os.environ['CFAS_TOKEN']
    secret = os.environ['CFAS_SECRET']
    org_name = os.environ.get('CFAS_ORG_NAME', '')
    space_name = os.environ.get('CFAS_SPACE_NAME', '')
    app_id = os.environ.get(
        'CFAS_APP_ID', app_id)
    space_id = os.environ.get(
        'CFAS_SPACE_ID', space_id)
    validate_ssl = _parse_bool(os.environ.get(
        'CFAS_VALIDATE_SSL', validate_ssl))
    scaling_monitor_interval = int(os.environ.get(
        'CFAS_SCALING_MONITOR_INTERVAL', scaling_monitor_interval))
    scaling_min_instances = int(os.environ.get(
        'CFAS_SCALING_MIN_INSTANCES', scaling_min_instances))
    scaling_max_instances = int(os.environ.get(
        'CFAS_SCALING_MAX_INSTANCES', scaling_max_instances))


def get_old_config(ignore_parse_failure=True):
    global validate_ssl
    global secret
    global token
    global autoscaler_api_url
    global scaling_monitor_interval
    global scaling_min_instances
    global scaling_max_instances

    config = {}
    filename = path.normpath(path.dirname(__file__) + '/../config.yml')
    try:
        with open(filename) as f:
            config = yaml.load(f)
    except Exception as e:
        print('Failed to parse config file {0}'.format(filename))
        print(str(e))
        if not ignore_parse_failure:
            raise e

    autoscaler_api_url = config.get('autoscaler_api_url', autoscaler_api_url)
    secret = config.get('secret', secret)
    token = config.get('token', token)
    validate_ssl = _parse_bool(config.get('validate_ssl', validate_ssl))
    _scaling = config.get('scaling', {})
    scaling_monitor_interval = _scaling.get(
        'monitor_interval', scaling_monitor_interval)
    scaling_min_instances = _scaling.get(
        'min_num_instances', scaling_min_instances)
    scaling_max_instances = _scaling.get(
        'max_num_instances', scaling_max_instances)


get_env_config()
get_old_config()
get_scaling_num_instances()
get_config_vcap_application()
