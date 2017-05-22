#! /bin/bash
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

if [ -z ${1+present} ]; then
  echo "Starting *without* mapping host source tree to docker."
  echo "If you want to do that, pass one argument with path to source on host"
  docker run -t -d --volumes-from basalt-data-store --name basalt-container -p 80:80 -p 443:443 -p 3306:3306 -p 5984:5984 -p 8080:8080 -p 9090:9090 -p 8181:8181 -p 9191:9191 -p 5000:5000 -p 222:22 xgds-basalt-sse
else
  echo "Starting with host source tree at $1 mapped into docker."
  docker run -t -d -v $1:/home/xgds/xgds_basalt --volumes-from basalt-data-store --name basalt-container -p 80:80 -p 443:443 -p 3306:3306 -p 5984:5984 -p 8080:8080 -p 9090:9090 -p 8181:8181 -p 9191:9191 -p 5000:5000 -p 222:22 xgds-basalt-sse
fi
