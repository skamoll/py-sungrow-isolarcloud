"""Tests for async ISolarCloudClient with mocked HTTP responses."""

from __future__ import annotations

import json
from typing import Any

import pytest

from custom_components.py_sungrow_isolarcloud.api import (
    ISolarCloudAuthError,
    ISolarCloudClient,
)


class _FakeResponse:
    def __init__(self, status: int, body: dict[str, Any], headers: dict[str, str] | None = None):
        self.status = status
        self._body = json.dumps(body)
        self.headers = headers or {}

    async def text(self) -> str:
        return self._body

    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _FakeSession:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, dict[str, str]]] = []

    def post(self, url: str, data: str, headers: dict[str, str], timeout: Any) -> _FakeResponse:
        self.calls.append((url, headers))
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_login_and_fetch_all_plants() -> None:
    """Client logs in, fetches plants, plant flow, and device list."""
    session = _FakeSession(
        [
            _FakeResponse(
                200,
                {
                    "result_code": "1",
                    "result_msg": "success",
                    "result_data": {"token": "abc_123", "user_id": "999"},
                },
            ),
            _FakeResponse(
                200,
                {
                    "result_code": "1",
                    "result_msg": "success",
                    "result_data": {
                        "pageList": [
                            {"ps_id": "6116893", "ps_name": "Casa", "ps_status": 1},
                        ]
                    },
                },
            ),
            _FakeResponse(
                200,
                {
                    "result_code": "1",
                    "result_msg": "success",
                    "result_data": {
                        "pv_power_map": {"value": "3.2", "unit": "kW"},
                        "battery_level_percent": "75",
                    },
                },
            ),
            _FakeResponse(
                200,
                {
                    "result_code": "1",
                    "result_msg": "success",
                    "result_data": {
                        "pageList": [
                            {
                                "ps_key": "6116893_14_1_1",
                                "device_name": "Inverter",
                                "device_type": 14,
                                "device_status": 1,
                                "fault_status": "4",
                            }
                        ]
                    },
                },
            ),
            _FakeResponse(
                200,
                {
                    "result_code": "1",
                    "result_msg": "success",
                    "result_data": [
                        {
                            "point_id": 13003,
                            "point_name": "Total DC power",
                            "unit": "W",
                            "value": "1200",
                        },
                        {
                            "point_id": 13146,
                            "point_name": "Operating status",
                            "unit": "",
                            "value": "Grid-connected operation",
                            "flag": "enum",
                        },
                    ],
                },
            ),
            _FakeResponse(
                200,
                {
                    "result_code": "1",
                    "result_msg": "success",
                    "result_data": {
                        "weather_map": {
                            "current_temperature_c": 17,
                            "sunrise": "07:42",
                            "weather_code": "0",
                        },
                        "weather_info_list": [
                            {"high_temperature": 19, "low_temperature": 5},
                        ],
                    },
                },
            ),
            _FakeResponse(
                200,
                {
                    "result_code": "1",
                    "result_msg": "success",
                    "result_data": {"data_info": {"data_detail_list": []}},
                },
            ),
        ]
    )

    client = ISolarCloudClient(session, "user@example.com", "secret", gateway="eu")  # type: ignore[arg-type]
    data = await client.async_fetch_all_plants()

    assert "6116893" in data
    plant = data["6116893"]
    assert plant.summary.ps_name == "Casa"
    assert plant.flow.pv_power.value == 3.2
    assert plant.flow.battery_soc == 75.0
    assert len(plant.devices) == 1
    assert plant.devices[0].ps_key == "6116893_14_1_1"
    assert plant.devices[0].points[13003].value == 1200.0
    assert plant.devices[0].points[13146].value == "Grid-connected operation"
    assert session.calls[0][0] == "https://gateway.isolarcloud.eu/v1/userService/login"


@pytest.mark.asyncio
async def test_login_invalid_credentials_raises_auth_error() -> None:
    """Invalid credentials raise ISolarCloudAuthError without looping."""
    session = _FakeSession(
        [
            _FakeResponse(
                200,
                {
                    "result_code": "010",
                    "result_msg": "Incorrect account or password",
                },
            )
        ]
    )
    client = ISolarCloudClient(session, "user@example.com", "wrong", gateway="eu")  # type: ignore[arg-type]
    with pytest.raises(ISolarCloudAuthError):
        await client.async_login()
