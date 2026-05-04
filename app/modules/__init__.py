"""Feature modules - plug-and-play application features"""

# Import submodules to ensure they're available
from . import auth
from . import agents
from . import knowledge_bases
from . import rag

__all__ = ["auth", "agents", "knowledge_bases", "rag"]
