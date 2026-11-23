"""Structural tests for Home Assistant manifest, HACS, and translations."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMP = ROOT / "custom_components" / "py_sungrow_isolarcloud"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_manifest_and_hacs() -> None:
    """Validate manifest.json and hacs.json required fields."""
    manifest = _load_json(COMP / "manifest.json")
    hacs = _load_json(ROOT / "hacs.json")

    assert manifest["domain"] == "py_sungrow_isolarcloud"
    assert manifest["config_flow"] is True
    assert manifest["iot_class"] == "cloud_polling"
    assert manifest["requirements"] == []
    assert hacs["name"] == "Sungrow iSolarCloud"


def test_translations_parity() -> None:
    """Ensure strings.json, en.json, and es.json have identical key structures."""
    strings = _load_json(COMP / "strings.json")
    en = _load_json(COMP / "translations" / "en.json")
    es = _load_json(COMP / "translations" / "es.json")

    assert strings == en
    assert set(strings.keys()) == set(es.keys())
    assert set(strings["entity"]["sensor"].keys()) == set(es["entity"]["sensor"].keys())
    assert set(strings["entity"]["binary_sensor"].keys()) == set(
        es["entity"]["binary_sensor"].keys()
    )
    assert set(strings["selector"]["gateway"]["options"].keys()) == set(
        es["selector"]["gateway"]["options"].keys()
    )


def test_entity_translation_keys_exist() -> None:
    """Every translation_key in sensor.py and binary_sensor.py exists in strings.json."""
    strings = _load_json(COMP / "strings.json")

    sensor_src = (COMP / "sensor.py").read_text(encoding="utf-8")
    sensor_keys = set(re.findall(r'translation_key="([^"]+)"', sensor_src))
    assert sensor_keys <= set(strings["entity"]["sensor"].keys())

    binary_src = (COMP / "binary_sensor.py").read_text(encoding="utf-8")
    binary_keys = set(re.findall(r'_attr_translation_key\s*=\s*"([^"]+)"', binary_src))
    assert binary_keys <= set(strings["entity"]["binary_sensor"].keys())
