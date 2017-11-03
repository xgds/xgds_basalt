
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
from basaltApp.register import renderTemplate

urlpatterns = [url(r'^$', renderTemplate, {'template_name':'basaltApp/index.html'}, 'index'),
               url(r'^setup$', TemplateView.as_view(template_name='basaltApp/setup.html'), {}, 'setup_intro'),
               url(r'^editEV/?$', views.editEV, {}, 'planner2_edit_ev'),
               url(r'^editEV/(?P<pk>[\d]+)$', views.editEV, {}, 'planner2_re_edit_ev'),
               url(r'^saveEV/?$', views.editEV, {}, 'planner2_save_ev'),
               url(r'^saveEV/(?P<pk>[\d]+)$', views.editEV, {}, 'planner2_re_save_ev'),
               url(r'^pextant/(?P<planId>[\d]+)$', views.callPextantAjax, {},'pextant_ajax'),
               url(r'^pextant/(?P<planId>[\d]+)/(?P<clear>[\d])$', views.callPextantAjax, {},'pextant_ajax_clear'),
               url(r'^storeFieldData$', views.storeFieldData, {}, 'storeFieldData'),
               url(r'^live', views.getLiveIndex, {}, 'basalt_live'),
               url(r'^objectsLive', views.getLiveObjects, {}, 'basalt_live_objects'),
               url(r'^activePlan/(?P<vehicleName>\w*)$', views.getActivePlan, {}, 'basalt_live_objects'),
               url(r'^w$', views.wrist, {'fileFormat':'.kml'}, 'wrist'),
               # get instrument import page
               url(r'^instrumentDataImport/(?P<instrumentName>\w*)$', views.getInstrumentDataImportPage, name="get_instrument_data_import_page"),
               url(r'^pXRFDataImport/$', views.getPxrfDataImportPage, name="get_pxrf_data_import_page"),
    
               #get instrument edit page
               url(r'^edit/(?P<instrument_name>\w*)/(?P<pk>[\d]+)$', views.editInstrumentData, name="instrument_data_edit"),
               # update instrument data
               url(r'^pextantTest/$', TemplateView.as_view(template_name='basaltApp/pextantTest.html'), {}, 'pextantTest'),
               
               # Including these in this order ensures that reverse will return the non-rest urls for use in our server
               url(r'^rest/', include('basaltApp.restUrls')),
               url('', include('basaltApp.restUrls')),


           ]
