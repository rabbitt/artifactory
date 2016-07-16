import sys
import types
import hashlib
from contextlib import contextmanager

def export(symbol):
  caller_module = sys._getframe(1).f_globals

  if caller_module['__name__'] == '__main__':
    # no need to export symbol if we're in __main__
    return symbol
    
  if not '__all__' in caller_module:
    caller_module['__all__'] = []

  try:
    caller_module['__all__'].append(symbol.__name__)
  except AttributeError:
    caller_module['__all__'].append(symbol)

  return symbol

def isclass(klass):
  try:
    # python 3 doesn't have types.ClassType, which is what python 2
    # used to differentiate between classic classes and new style classes.
    # if this raises an AttributeError, it means we're in python 3.
    return isinstance(klass, (type, types.ClassType))
  except AttributeError:
    return isinstance(klass, type)

@export
def merge_dicts(*args):
    result = {}
    for _dict in args:
        result.update(_dict)
    return result

@export
class Singleton(type):
  _instances = {}
  
  def __call__(cls, *args, **kwargs):
    if cls not in cls._instances:
      cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
    return cls._instances[cls]

@export
def singleton(klass):
  if isclass(klass):
    klass.__metaclass__ = Singleton
  return klass

@export
def md5sum(filename):
    """
    Calculates md5 hash of a file
    """
    return hexdigest(filename, 'md5')

@export
def sha1sum(filename):
    """
    Calculates sha1 hash of a file
    """
    return hexdigest(filename, 'sha1')

@export
def sha256sum(filename):
    """
    Calculates sha256 hash of a file
    """
    return hexdigest(filename, 'sha256')

@export
def sha512sum(filename):
    """
    Calculates sha1 hash of a file
    """
    return hexdigest(filename, 'sha512')

def hexdigest(filename, hash_type):
  hasher = getattr(hashlib, hash_type)()
  with open(filename, 'rb') as f:
    for chunk in iter(lambda: f.read(128 * hasher.block_size), b''):
      hasher.update(chunk)
  return hasher.hexdigest()
