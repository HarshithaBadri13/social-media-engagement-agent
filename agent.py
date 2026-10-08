"""Compatibility import for code that still uses ``import agent``."""
from backend.agent import *
try:
    from backend.database import get_brand_profile, save_brand_profile, reset_brand_profile
except ImportError:
    pass