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

from django.conf.urls import url
from django.contrib import auth

from basaltApp import register

urlpatterns = [url(r'^login/$', auth.views.login, {}, 'user-login'),
               url(r'^logout/$', auth.views.logout, {'next_page': '/basaltApp/'}, 'user-logout'),
               url(r'^register/$', register.registerUser, {}, 'user-registration'),
               url(r'^activate/(.*)$', register.activateUser, {}, 'user-activate'),
               url(r'^reset-password/$', auth.views.password_reset, {}, 'reset-password'),
               url(r'^reset-password-done/$', auth.views.password_reset_done, {},'password_reset_done'),
               url(r'^reset-password-confirm/(?P<uidb36>[^/]+)/(?P<token>.+)$', auth.views.password_reset_confirm, {}, 'django.contrib.auth.views.password_reset_confirm'),
               url(r'^reset-password-complete/$', auth.views.password_reset_complete, {}),
               url(r'^feedback/$', register.email_feedback, {}, 'email_feedback'),
               url(r'^rest/genToken/(?P<username>[\w]*)$', register.generateAuthToken, {}, 'user-gen-token'),
               url(r'^genToken/(?P<username>[\w]*)$', register.generateAuthToken, {}, 'user-gen-token'),
           ]
