
from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.storage import FileSystemStorage
from collections import OrderedDict
import os

# Copy-pasted from:
# https://github.com/django/django/blob/master/django/contrib/staticfiles/finders.py
class NpmAppFinder(FileSystemFinder):
    """
    A static files finder that looks in the directory of each app as
    specified in the source_dir attribute.
    """
    storage_class = FileSystemStorage
    source_dir = 'static'

    def __init__(self, app_names=None, *args, **kwargs):
        # The list of apps that are handled
        self.apps = []
        # Mapping of app names to storage instances
        self.storages = OrderedDict()
        app_configs = apps.get_app_configs()
        if app_names:
            app_names = set(app_names)
            app_configs = [ac for ac in app_configs if ac.name in app_names]
        for app_config in app_configs:
            app_storage = self.storage_class(
                os.path.join(app_config.path, self.source_dir))
            if os.path.isdir(app_storage.location):
                self.storages[app_config.name] = app_storage
                if app_config.name not in self.apps:
                    self.apps.append(app_config.name)
        super().__init__(*args, **kwargs)

    def list(self, ignore_patterns):
        """
        List all files in all app storages.
        """
        for storage in self.storages.values():
            if storage.exists(''):  # check if storage location exists
                for path in utils.get_files(storage, ignore_patterns):
                    yield path, storage

    def find(self, path, all=False):
        """
        Look for files in the app directories.
        """
        matches = []
        for app in self.apps:
            app_location = self.storages[app].location
            if app_location not in searched_locations:
                searched_locations.append(app_location)
            match = self.find_in_app(app, path)
            if match:
                if not all:
                    return match
                matches.append(match)
        return matches

    def find_in_app(self, app, path):
        """
        Find a requested static file in an app's static locations.
        """
        storage = self.storages.get(app)
        if storage:
            # only try to find a file if the source dir actually exists
            if storage.exists(path):
                matched_path = storage.path(path)
                if matched_path:
                    return matched_path