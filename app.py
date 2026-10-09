"""Compatibility entry point for ``streamlit run app.py``."""
import sys
from pathlib import Path

# Ensure workspace root is always on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Execute frontend/app.py in the main execution context
_app_file = ROOT_DIR / "frontend" / "app.py"
with open(_app_file, "r", encoding="utf-8") as _f:
    exec(compile(_f.read(), str(_app_file), "exec"), globals())