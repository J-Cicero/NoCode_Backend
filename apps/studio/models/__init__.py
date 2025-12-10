from .project import Project
from .table import Table
from .attribute import Attribute
from .page import Page
from .component import Component
from .component_instance import ComponentInstance
from .collaboration import EditLock, CollaborationSession

# Backward compatibility aliases
DataSchema = Table
FieldSchema = Attribute
