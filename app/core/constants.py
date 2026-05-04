"""Application constants"""

# API Versioning
API_V1_PREFIX = "/api/v1"

# Database
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache TTL (seconds)
CACHE_TTL_SHORT = 300    # 5 minutes
CACHE_TTL_MEDIUM = 3600  # 1 hour
CACHE_TTL_LONG = 86400   # 1 day

# Role-based access control
ROLES = {
    "admin": 1,
    "manager": 2,
    "user": 3,
    "guest": 4
}
