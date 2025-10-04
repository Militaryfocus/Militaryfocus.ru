"""
API endpoints package
"""
from . import auth
from . import posts
from . import comments
from . import categories
from . import tags
from . import users
from . import uploads

__all__ = ['auth', 'posts', 'comments', 'categories', 'tags', 'users', 'uploads']