import os
import sys

# Ensure repository root and backend directory are on sys.path so tests
# can import `backend` and top-level packages like `agent_framework`.
HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BACKEND_DIR = os.path.join(ROOT, "backend")

for p in (BACKEND_DIR, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
