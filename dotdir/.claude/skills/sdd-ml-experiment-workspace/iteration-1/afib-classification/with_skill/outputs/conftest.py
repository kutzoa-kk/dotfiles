"""Root conftest -- ensures src is importable from tests."""

import sys
from pathlib import Path

# Add experiment root to Python path so `from src.xxx import yyy` works
sys.path.insert(0, str(Path(__file__).parent))
