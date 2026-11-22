"""Pytest configuration allowing API tests to run with or without Home Assistant installed."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

if importlib.util.find_spec("homeassistant") is None:
    root = Path(__file__).resolve().parent.parent
    cc_pkg = types.ModuleType("custom_components")
    cc_pkg.__path__ = [str(root / "custom_components")]
    sys.modules.setdefault("custom_components", cc_pkg)

    comp_pkg = types.ModuleType("custom_components.py_sungrow_isolarcloud")
    comp_pkg.__path__ = [str(root / "custom_components" / "py_sungrow_isolarcloud")]
    sys.modules.setdefault("custom_components.py_sungrow_isolarcloud", comp_pkg)
