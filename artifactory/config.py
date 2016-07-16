import os
import yaml

from . import utils
from . import urls

from .exceptions import *
from .utils import export, singleton

@export
@singleton
class ArtifactoryConfig(dict):
  def __init__(self, *args, **kwargs):
    self.update(*args, **kwargs)

  def __getitem__(self, key):
    search_key = self.search(key) if key not in self else key
    return self.get(search_key, None)
    
  def __setitem__(self, key, value):
    raise ImmutableConfigError("attempt to change value on immutable config object")

  def __repr__(self):
    dictrepr = dict.__repr__(self)
    return 'Config(%s)' % dictrepr

  def search(self, search, separator='/'):
    search_url = urls.urlparse(search).protoless_url
    for entry in self:
      entry_url = urls.urlparse(entry).protoless_url.rstrip(separator)
      if search_url.startswith(entry_url):
        return entry
    return None

  @property
  def to_yaml(self):
    return yaml.dump(dict(self))
  
  def load_file(self, file_path):
    """
    Read configuration file and produce a dictionary of the following structure:
      ---
      http://foo.bar.com/artifactory:
        username: '<username>'
        password: '<password>'
        verify: true/false
        cert: /path/to/certificate
      http://bar.baz.com/:
        ...

    config-path - file, or specifies where to read the config from
    """
    return self.load_yaml(file(file_path))
  
  def load_yaml(self, yaml_data):
    """
    Takes a yaml structured string, converts it to a dictionary and loads it into the config
    """
    return self.load(yaml.load(yaml_data))
  
  def clear(self):
    super(ArtifactoryConfig, self).clear()
    return self
    
  def load(self, data_dict):
    """
    Merges the provides dictionary into the config
    """
    self.update(data_dict)

    for key in self:
      data = self.get(key, {})
      cert = None
      if 'cert' in data and data['cert']:
        cert = os.path.expanduser(data.get('cert'))
      data.update({
        'username': data.get('username', None),
        'password': data.get('password', None),
        'verify':   data.get('verify', True),
        'cert':     cert
      })
    
    return self

Config = ArtifactoryConfig()
