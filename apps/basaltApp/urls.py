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

from django.conf.urls import include, url

from django.views.generic.base import TemplateView
from basaltApp import views

urlpatterns = [url(r'^$', TemplateView.as_view(template_name='basaltApp/index.html'), {}, 'index'),
               url(r'^editEV/?$', views.editEV, {}, 'planner2_edit_ev'),
               url(r'^editEV/(?P<pk>[\d]+)$', views.editEV, {}, 'planner2_re_edit_ev'),
               url(r'^saveEV/?$', views.editEV, {}, 'planner2_save_ev'),
               url(r'^saveEV/(?P<pk>[\d]+)$', views.editEV, {}, 'planner2_re_save_ev'),
               url(r'^pextant/(?P<planId>[\d]+)$', views.callPextantAjax, {},
                   'pextant_ajax'),
               url(r'^storeFieldData$', views.storeFieldData, {}, 'storeFieldData')
           ]
