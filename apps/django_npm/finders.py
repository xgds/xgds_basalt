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
import fnmatch
from django.contrib.staticfiles.finders import AppDirectoriesFinder


class NpmAppFinder(AppDirectoriesFinder):
    """
    A static files finder that looks in the directory of each app as
    specified in the source_dir attribute.
    """
    source_dir = 'node_modules'
    dependency_sets = {}
    modules_names = set()

    def load_dependencies(self, storage):
        if not os.path.basename(storage.location) == self.source_dir:
            return set()

        package_dir = os.path.dirname(storage.location)
        package_path = os.path.join(package_dir, 'package.json')

        if not os.path.exists(package_path):
            return set()

        package = json.load(open(package_path))

        if 'dependencies' not in package:
            return set()

        deps = set(package['dependencies'].keys()) - self.modules_names
        self.modules_names |= deps

        django_config = {}
        if 'django' in package:
            django_config = package['django']

        return deps, django_config

    def matches_filters(self, path, filters):
        if 'include' in filters:
            includes = filters['include']
            for include in includes:
                if fnmatch.fnmatchcase(path, include):
                    return True
            return False

        if 'exclude' in filters:
            excludes = filters['exclude']
            for exclude in excludes:
                if fnmatch.fnmatchcase(path, exclude):
                    return False

        return True

    def is_dependency(self, path, storage):
        if storage.location not in self.dependency_sets:
            self.dependency_sets[storage.location] = self.load_dependencies(storage)
        parts = path.split(os.sep)
        module_name = parts[0]
        remaining_path = os.sep.join(parts[1:])
        dependencies, filters = self.dependency_sets[storage.location]

        if module_name not in dependencies:
            return False

        if module_name in filters:
            return self.matches_filters(remaining_path, filters[module_name])

        return True

    def list(self, ignore_patterns):
        """
        List all files in all app storages.
        """
        for path, storage in AppDirectoriesFinder.list(self, ignore_patterns):
            if self.is_dependency(path, storage):
                yield path, storage
