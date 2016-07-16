try:
  # try python 3 variant first
  import urllib.parse
  import urllib.parse as urlparse
except ImportError:
  # fallback to python 2 variant
  import urlparse
  
from .utils import export
from copy import deepcopy as copy

__all__ = copy(urlparse.__all__)

@export
def protoless_url(url):
  """
  Returns a URL without the http:// or https:// prefixes
  """
  return urlparse(url).protoless_url

class ParseResult(urlparse.ParseResult):
  @property
  def proto_relative_url(self):
    try:
      return filter(None, self.geturl().partition(':')[::2])[-1]
    except TypeError:
      return tuple(filter(None, self.geturl().partition(':')[::2]))[-1]

  @property
  def protoless_url(self):
    try:
      return filter(None, self.geturl().partition('://')[::2])[-1]
    except TypeError:
      return tuple(filter(None, self.geturl().partition('://')[::2]))[-1]
      
class SplitResult(urlparse.SplitResult):
  @property
  def proto_relative_url(self):
    try:
      return filter(None, self.geturl().partition(':')[::2])[-1]
    except TypeError:
      return tuple(filter(None, self.geturl().partition(':')[::2]))[-1]

  @property
  def protoless_url(self):
    try:
      return filter(None, self.geturl().partition('://')[::2])[-1]
    except TypeError:
      return tuple(filter(None, self.geturl().partition('://')[::2]))[-1]

try:
  # try python 3 variant first
  urllib.parse.ParseResult = ParseResult
  urllib.parse.SplitResult = SplitResult
except NameError:
  # fallback to python 2 variant
  urlparse.ParseResult = ParseResult
  urlparse.SplitResult = SplitResult

# reimport everything and then export it all
try:
  # try python 3 variant first
  from urllib.parse import *
except ImportError:
  # fallback to python 2 variant
  from urlparse import *
