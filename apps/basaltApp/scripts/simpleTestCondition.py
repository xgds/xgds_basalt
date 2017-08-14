#! /usr/bin/env python

#__BEGIN_LICENSE__
# Copyright (c) 2015, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The xGDS platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#__END_LICENSE__

import sys
import requests
import datetime
import json
import pytz

HTTP_PREFIX = 'https'
URL_PREFIX = 'localhost'

def test_set_condition():
    url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
    nowtime = datetime.datetime.now(pytz.utc)
    isonow = nowtime.isoformat()
    nested_data_dict = {'start_time': isonow,
                        'status': 'activity_started',
                        'timezone': 'US/Hawaii',
                        'name': 'test_set_condition',
                        'extra': 'Start time should be set',
                        'assignment': 'EV2',
                        'group_name': '20170807A',
                        'xgds_id': 'HIL13_A_WAY0_0_PXO'
                        }
    data = {'time': isonow,
            'source': 'playbook',
            'id': 'PB1',
            'data': json.dumps(nested_data_dict)
            }
    response = requests.post(url, data=data, verify=False)
    json_response = response.json()
    return json_response

def test_update_condition():
    url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
    nowtime = datetime.datetime.now(pytz.utc)
    isonow = nowtime.isoformat()
    nested_data_dict = {'status': 'activity_in_progress',
                        'extra': 'In progress for this',
                        'assignment': 'EV2',
                        'group_name': '20170807A',
                        'xgds_id': 'HIL13_A_WAY0_0_PXO'
                        }
    data = {'time': isonow,
            'source': 'playbook',
            'id': 'PB1',
            'data': json.dumps(nested_data_dict)
            }
    response = requests.post(url, data=data, verify=False)
    json_response = response.json()
    return json_response

def test_abort_condition():
    url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
    nowtime = datetime.datetime.now(pytz.utc)
    isonow = nowtime.isoformat()
    nested_data_dict = {'status': 'activity_aborted',
                        'extra': 'Dead dead dead like a doornail',
                        'assignment': 'EV2',
                        'group_name': '20170807A',
                        'xgds_id': 'HIL13_A_WAY0_0_PXO'
                        }
    data = {'time': isonow,
            'source': 'playbook',
            'id': 'PB1',
            'data': json.dumps(nested_data_dict)
            }
    response = requests.post(url, data=data, verify=False)
    json_response = response.json()
    return json_response

def test_end_condition():
    url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
    nowtime = datetime.datetime.now(pytz.utc)
    isonow = nowtime.isoformat()
    nested_data_dict = {'end_time': isonow,
                        'status': 'activity_completed',
                        'extra': 'Done done done',
                        'assignment': 'EV2',
                        'group_name': '20170807A',
                        'xgds_id': 'HIL13_A_WAY0_0_PXO'
                        }
    data = {'time': isonow,
            'source': 'playbook',
            'id': 'PB1',
            'data': json.dumps(nested_data_dict)
            }
    response = requests.post(url, data=data, verify=False)
    json_response = response.json()
    return json_response


mode = sys.argv[1]
print "Running %s condition check..." % mode

if mode == 'set':
    resp = test_set_condition()
if mode == 'update':
    resp = test_update_condition()
if mode == 'end':
    resp = test_end_condition()
if mode == 'abort':
    resp = test_abort_condition()

print "response:", resp
