"""Root conftest for knee-oa-progression tests."""

import sys
from pathlib import Path

# Ensure experiment root is on Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
