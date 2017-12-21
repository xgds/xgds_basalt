# __BEGIN_LICENSE__
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
# __END_LICENSE__

import os
import json
from django.contrib.staticfiles.finders import AppDirectoriesFinder


class NpmAppFinder(AppDirectoriesFinder):
    """
    A static files finder that looks in the directory of each app as
    specified in the source_dir attribute.
    """
    source_dir = 'node_modules'
    dependency_sets = {}

    def load_dependencies(self, storage):
        if not os.path.basename(storage.location) == self.source_dir:
            return set()

        package_dir = os.path.dirname(storage.location)
        package_path = os.path.join(package_dir, 'package.json')

        if not os.path.exists(package_path):
            return set()

        package = json.load(open(package_path))

        if not 'dependencies' in package:
            return set()

        return set(package['dependencies'].keys())

    def is_dependency(self, path, storage):
        if not storage.location in self.dependency_sets:
            self.dependency_sets[storage.location] = self.load_dependencies(storage)
        module_name = path.split(os.sep)[0]
        return module_name in self.dependency_sets[storage.location]

    def list(self, ignore_patterns):
        """
        List all files in all app storages.
        """
        for path, storage in AppDirectoriesFinder.list(self, ignore_patterns):
            if self.is_dependency(path, storage):
                yield path, storage
