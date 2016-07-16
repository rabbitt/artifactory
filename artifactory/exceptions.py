from .utils import export

@export 
class ArtifactoryError(Exception):
  pass
  
@export
class ImmutableConfigError(ArtifactoryError): 
  pass
