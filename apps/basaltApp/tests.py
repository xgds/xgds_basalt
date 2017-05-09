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
import requests
import datetime
import json
import pytz

from django.test import TestCase

HTTP_PREFIX = 'https'
URL_PREFIX = 'xgds-local.xgds.org'

def test_set():
    url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
    nowtime = datetime.datetime.now(pytz.utc)
    isonow = nowtime.isoformat()
    nested_data_dict = {'start_time': isonow,
                        'status': 'started',
                        'timezone': 'US/Hawaii',
                        'name': 'test_set_condition',
                        'extra': 'Start time should be set',
                        'assignment': 'EV2',
                        'group_name': '20170426B',
                        'xgds_id': 'HIL13_A_WAY0_0_PXO'
                        }
    data = {'time': isonow,
            'source': 'playbook',
            'id': 'PB1',
            'data': json.dumps(nested_data_dict)
            }
    response = requests.post(url, data=data)
    
def test_progress():
    url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
    nowtime = datetime.datetime.now(pytz.utc)
    isonow = nowtime.isoformat()
    nested_data_dict = {'status': 'in_progress',
                        'extra': 'In progress for this',
                        'assignment': 'EV2',
                        'group_name': '20170426B',
                        'xgds_id': 'HIL13_A_WAY0_0_PXO'
                        }
    data = {'time': isonow,
            'source': 'playbook',
            'id': 'PB1',
            'data': json.dumps(nested_data_dict)
            }
    response = requests.post(url, data=data)
    
def test_end():
    url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
    nowtime = datetime.datetime.now(pytz.utc)
    isonow = nowtime.isoformat()
    nested_data_dict = {'end_time': isonow,
                        'status': 'completed',
                        'extra': 'Done done done',
                        'assignment': 'EV2',
                        'group_name': '20170426B',
                        'xgds_id': 'HIL13_A_WAY0_0_PXO'
                        }
    data = {'time': isonow,
            'source': 'playbook',
            'id': 'PB1',
            'data': json.dumps(nested_data_dict)
            }
    response = requests.post(url, data=data)

class basaltAppTest(TestCase):
    
    """
    Tests for basaltApp
    """
    def test_basaltApp(self):
        pass
    
class basaltAppConditionSetTest(TestCase):
    
    def test_set_condition(self):
        from django.conf import settings

        url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
        nowtime = datetime.datetime.now(pytz.utc)
        isonow = nowtime.isoformat()
        nested_data_dict = {'start_time': isonow,
                            'status': 'Started',
                            'timezone': settings.TIME_ZONE,
                            'name': 'test_set_condition',
                            'extra': 'Start time should be set',
                            'assignment': 'EV2',
                            'group_name': '20170426B',
                            'xgds_id': 'HIL13_A_WAY0_0_PXO'
                            }
        data = {'time': isonow,
                'source': 'playbook',
                'id': 'PB1',
                'data': json.dumps(nested_data_dict)
                }
        response = requests.post(url, data=data)
        json_response = response.json()
        self.assertEqual(json_response['status'], 'success')
        condition_history_json = json_response['data']
        result_list = json.loads(condition_history_json)
        condition_dict = result_list[0]['fields']
        condition_history_dict = result_list[1]['fields']
        timestring = '%s.%3dZ' % (nowtime.strftime('%Y-%m-%dT%H:%M:%S'), nowtime.microsecond/1000)
        condition_history_jsonData = json.loads(condition_history_dict['jsonData'])
        self.assertEqual(condition_history_dict['status'], 'Started')
        self.assertEqual(condition_dict['name'], 'test_set_condition')
        self.assertEqual(condition_dict['xgds_id'], 'HIL13_A_WAY0_0_PXO')
        self.assertEqual(condition_dict['timezone'], settings.TIME_ZONE)
        self.assertEqual(condition_dict['vehicle'], 2)
        self.assertEqual(condition_dict['source_group_name'], '20170426B')
        self.assertEqual(condition_dict['flight'], 1481)
        
        self.assertEqual(condition_history_dict['source_time'], timestring)
#         self.assertEqual(condition_history_dict['jsonData'], json.dumps(data['data']))
        self.assertEqual(condition_history_jsonData['extra'], 'Start time should be set')
        self.assertEqual(condition_history_jsonData['assignment'], 'EV2')
        self.assertEqual(condition_history_jsonData['group_name'], '20170426B')
        self.assertEqual(condition_dict['start_time'], timestring)
        self.assertEqual(condition_dict['source_id'], 'PB1')
        self.assertEqual(condition_dict['source'], 'playbook')

class basaltAppConditionUpdateTest(TestCase):

    def test_update_condition(self):
        from django.conf import settings

        url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
        nowtime = datetime.datetime.now(pytz.utc)
        isonow = nowtime.isoformat()
        nested_data_dict = {'status': 'in_progress',
                            'extra': 'In progress for this',
                            'assignment': 'EV2',
                            'group_name': '20170426B',
                            'xgds_id': 'HIL13_A_WAY0_0_PXO'
                            }
        data = {'time': isonow,
                'source': 'playbook',
                'id': 'PB1',
                'data': json.dumps(nested_data_dict)
                }
        response = requests.post(url, data=data)
        json_response = response.json()
        self.assertEqual(json_response['status'], 'success')
        condition_history_json = json_response['data']
        result_list = json.loads(condition_history_json)
        condition_dict = result_list[0]['fields']
        condition_history_dict = result_list[1]['fields']
        timestring = '%s.%3dZ' % (nowtime.strftime('%Y-%m-%dT%H:%M:%S'), nowtime.microsecond/1000)
        condition_history_jsonData = json.loads(condition_history_dict['jsonData'])
        
        self.assertEqual(condition_history_dict['status'], 'in_progress')
        self.assertEqual(condition_dict['name'], 'test_set_condition')
        self.assertEqual(condition_dict['xgds_id'], 'HIL13_A_WAY0_0_PXO')
        self.assertEqual(condition_dict['timezone'], settings.TIME_ZONE)
        self.assertEqual(condition_history_dict['source_time'], timestring)
#         self.assertEqual(condition_history_dict['jsonData'], json.dumps(data['data']))
        self.assertEqual(condition_history_jsonData['extra'], 'In progress for this')
        self.assertEqual(condition_history_jsonData['assignment'], 'EV2')
        self.assertEqual(condition_history_jsonData['group_name'], '20170426B')
        self.assertEqual(condition_dict['source_id'], 'PB1')
        self.assertEqual(condition_dict['source'], 'playbook')

class basaltAppConditionEndTest(TestCase):

    def test_update_condition(self):
        from django.conf import settings

        url = "%s://%s%s" % (HTTP_PREFIX, URL_PREFIX, '/xgds_core/condition/set/')
        nowtime = datetime.datetime.now(pytz.utc)
        isonow = nowtime.isoformat()
        nested_data_dict = {'end_time': isonow,
                            'status': 'completed',
                            'extra': 'Done done done',
                            'assignment': 'EV2',
                            'group_name': '20170426B',
                            'xgds_id': 'HIL13_A_WAY0_0_PXO'
                            }
        data = {'time': isonow,
                'source': 'playbook',
                'id': 'PB1',
                'data': json.dumps(nested_data_dict)
                }
        response = requests.post(url, data=data)
        json_response = response.json()
        self.assertEqual(json_response['status'], 'success')
        condition_history_json = json_response['data']
        result_list = json.loads(condition_history_json)
        condition_dict = result_list[0]['fields']
        condition_history_dict = result_list[1]['fields']
        timestring = '%s.%3dZ' % (nowtime.strftime('%Y-%m-%dT%H:%M:%S'), nowtime.microsecond/1000)
        condition_history_jsonData = json.loads(condition_history_dict['jsonData'])
        
        self.assertEqual(condition_history_dict['status'], 'completed')
        self.assertEqual(condition_dict['name'], 'test_set_condition')
        self.assertEqual(condition_dict['xgds_id'], 'HIL13_A_WAY0_0_PXO')
        self.assertEqual(condition_dict['timezone'], settings.TIME_ZONE)
        self.assertEqual(condition_history_dict['source_time'], timestring)
#         self.assertEqual(condition_history_dict['jsonData'], json.dumps(data['data']))
        self.assertEqual(condition_history_jsonData['extra'], 'In progress for this')
        self.assertEqual(condition_history_jsonData['assignment'], 'EV2')
        self.assertEqual(condition_history_jsonData['group_name'], '20170426B')
        self.assertEqual(condition_dict['source_id'], 'PB1')
        self.assertEqual(condition_dict['source'], 'playbook')
        self.assertEqual(condition_dict['end_time'], timestring)
        


        
