#!/usr/bin/env python3
"""运行 Spectrum 集成测试。"""

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SPECTRUM_USE_RUST", "1")

if __name__ == "__main__":
    verbosity = 2 if os.environ.get("VERBOSE") else 2
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
