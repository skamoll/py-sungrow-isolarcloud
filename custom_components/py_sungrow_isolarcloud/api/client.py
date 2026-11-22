"""Async HTTP client for iSolarCloud."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import aiohttp

from .const import (
    AUTO_GATEWAY_ORDER,
    DEFAULT_ACCESS_KEY,
    DEFAULT_APP_KEY,
    DEFAULT_USER_AGENT,
    DEFAULT_WEB_VERSION,
    ENDPOINT_GET_PS_ALL_DEVICE_LIST,
    ENDPOINT_GET_PS_DETAIL_WITH_PS_TYPE,
    ENDPOINT_GET_PS_LIST,
    ENDPOINT_LOGIN,
    GATEWAY_AUTO,
    GATEWAYS,
)
from .crypto import (
    aes_decrypt_hex,
    aes_encrypt_hex,
    current_gmt_header,
    current_timestamp_ms,
    generate_aes_key,
    generate_did,
    generate_nonce,
    rsa_encrypt_base64,
)
from .models import AuthSession, DeviceSummary, PlantData, PlantFlow, PlantSummary

_LOGGER = logging.getLogger(__name__)

_TOKEN_INVALID_CODES = {"E00003"}
_TOKEN_INVALID_MSGS = ("er_token_login_invalid", "need to login again")
_AUTH_FAILED_MSGS = ("account or password", "user_account", "er_invalid_appkey", "e914")


class ISolarCloudError(Exception):
    """Base iSolarCloud client exception."""


class ISolarCloudAuthError(ISolarCloudError):
    """Raised when credentials are invalid or authentication fails."""


class ISolarCloudConnectionError(ISolarCloudError):
    """Raised on network, timeout, or non-200 transport errors."""


class ISolarCloudApiError(ISolarCloudError):
    """Raised when iSolarCloud returns an API-level error."""


class ISolarCloudClient:
    """Async iSolarCloud client using AES+RSA encrypted JSON over HTTPS."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        gateway: str = GATEWAY_AUTO,
        app_key: str = DEFAULT_APP_KEY,
        lang: str = "_en_US",
        timeout_seconds: int = 30,
    ) -> None:
        self._http = session
        self._username = username
        self._password = password
        self._configured_gateway = gateway
        self._app_key = app_key
        self._lang = lang
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._did = generate_did()
        self._clock_offset_seconds = 0.0
        self._auth: AuthSession | None = None

    @property
    def active_gateway(self) -> str | None:
        """Return the currently authenticated gateway URL."""
        return self._auth.gateway if self._auth else None

    def _gateway_candidates(self) -> list[str]:
        if self._configured_gateway != GATEWAY_AUTO:
            resolved = GATEWAYS.get(self._configured_gateway, self._configured_gateway)
            return [resolved.rstrip("/")]
        if self._auth:
            ordered = [self._auth.gateway]
            for candidate in AUTO_GATEWAY_ORDER:
                if candidate not in ordered:
                    ordered.append(candidate)
            return ordered
        return list(AUTO_GATEWAY_ORDER)

    async def async_login(self) -> AuthSession:
        """Authenticate against configured or auto-discovered regional gateway."""
        last_error: Exception | None = None
        for base_url in self._gateway_candidates():
            try:
                payload = {
                    "user_account": self._username,
                    "user_password": self._password,
                    "login_type": "1",
                    "strong_weak_password": "1",
                    "rememberMe": False,
                    "supportTotp": 1,
                    "isNamePassword": True,
                    "sys_code": "900",
                }
                result = await self._post_encrypted(
                    base_url=base_url,
                    endpoint=ENDPOINT_LOGIN,
                    data=payload,
                    include_auth=False,
                )
                result_data = result.get("result_data") or {}
                token = str(result_data.get("token") or "")
                user_id = str(result_data.get("user_id") or "")
                if not token or not user_id:
                    raise ISolarCloudAuthError("Login succeeded without token or user_id")
                self._auth = AuthSession(
                    token=token,
                    user_id=user_id,
                    gateway=base_url,
                    login_at=datetime.now(UTC),
                )
                return self._auth
            except ISolarCloudAuthError:
                raise
            except (ISolarCloudConnectionError, ISolarCloudApiError) as err:
                _LOGGER.debug("Gateway %s login failed: %s", base_url, err)
                last_error = err
                continue

        if isinstance(last_error, ISolarCloudError):
            raise last_error
        raise ISolarCloudConnectionError("No iSolarCloud gateway succeeded")

    async def async_get_ps_list(self) -> list[PlantSummary]:
        """Fetch all plants accessible by the authenticated user."""
        data = await self._call_authed(
            ENDPOINT_GET_PS_LIST,
            {
                "curPage": 1,
                "size": 100,
                "valid_flag": "1,3",
            },
        )
        result_data = data.get("result_data") or {}
        rows = result_data.get("pageList") or []
        return [PlantSummary.from_dict(row) for row in rows if row.get("ps_id") is not None]

    async def async_get_ps_detail_with_ps_type(self, ps_id: str) -> PlantFlow:
        """Fetch curated plant power flow & energy totals."""
        data = await self._call_authed(
            ENDPOINT_GET_PS_DETAIL_WITH_PS_TYPE,
            {
                "ps_id": ps_id,
                "is_get_ps_level_data": "1",
                "version_tag": "1",
                "is_shut_down_flag": "1",
                "is_get_hm_info": "1",
                "func_code": "5",
            },
        )
        result_data = data.get("result_data") or {}
        return PlantFlow.from_detail_dict(result_data)

    async def async_get_ps_all_device_list(self, ps_id: str) -> list[DeviceSummary]:
        """Fetch device inventory for one plant."""
        data = await self._call_authed(
            ENDPOINT_GET_PS_ALL_DEVICE_LIST,
            {
                "ps_id": ps_id,
                "curPage": "1",
                "size": "100",
                "is_get_g2point5_inverter": "1",
                "is_get_second_level_flag": "1",
            },
        )
        result_data = data.get("result_data") or {}
        rows = result_data.get("pageList") or result_data.get("list") or []
        return [
            DeviceSummary.from_dict(ps_id, row)
            for row in rows
            if row.get("ps_key") or row.get("uuid")
        ]

    async def async_fetch_all_plants(self) -> dict[str, PlantData]:
        """Fetch plant summaries, flows, and devices for all plants."""
        if self._auth is None:
            await self.async_login()
        plants = await self.async_get_ps_list()
        output: dict[str, PlantData] = {}
        for plant in plants:
            flow = await self.async_get_ps_detail_with_ps_type(plant.ps_id)
            devices = await self.async_get_ps_all_device_list(plant.ps_id)
            output[plant.ps_id] = PlantData(summary=plant, flow=flow, devices=devices)
        return output

    async def _call_authed(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        if self._auth is None:
            await self.async_login()
        assert self._auth is not None
        try:
            return await self._post_encrypted(
                base_url=self._auth.gateway,
                endpoint=endpoint,
                data=data,
                include_auth=True,
            )
        except ISolarCloudAuthError:
            _LOGGER.debug("Session token expired on %s, re-authenticating once", endpoint)
            await self.async_login()
            return await self._post_encrypted(
                base_url=self._auth.gateway,
                endpoint=endpoint,
                data=data,
                include_auth=True,
            )

    async def _post_encrypted(
        self,
        base_url: str,
        endpoint: str,
        data: dict[str, Any],
        include_auth: bool,
        retry_clock: bool = True,
    ) -> dict[str, Any]:
        aes_key = generate_aes_key()
        body_dict: dict[str, Any] = {
            **data,
            "appkey": self._app_key,
            "lang": self._lang,
            "sys_code": data.get("sys_code", 200),
            "api_key_param": {
                "timestamp": current_timestamp_ms(self._clock_offset_seconds),
                "nonce": generate_nonce(),
            },
        }
        if include_auth and self._auth is not None:
            body_dict["token"] = self._auth.token
            body_dict["user_id"] = self._auth.user_id

        compact_json = json.dumps(body_dict, separators=(",", ":"))
        encrypted_body = aes_encrypt_hex(compact_json, aes_key)

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": DEFAULT_USER_AGENT,
            "origin": "https://www.isolarcloud.com",
            "referer": "https://www.isolarcloud.com/",
            "content-type": "text/plain;charset=UTF-8",
            "sys_code": "200",
            "_pl": "js",
            "_did": self._did,
            "_global_new_web": "1",
            "_vc": DEFAULT_WEB_VERSION,
            "_browser_brand": "chrome",
            "_browser_version": "132.0",
            "x-client-tz": current_gmt_header(),
            "x-sign-code": "0",
            "x-access-key": DEFAULT_ACCESS_KEY,
            "x-random-secret-key": rsa_encrypt_base64(aes_key),
        }
        if include_auth and self._auth is not None and self._auth.token:
            prefix = self._auth.token.split("_", 1)[0].strip()
            if prefix:
                headers["x-limit-obj"] = rsa_encrypt_base64(prefix)

        url = f"{base_url.rstrip('/')}{endpoint}"
        try:
            async with self._http.post(
                url,
                data=encrypted_body,
                headers=headers,
                timeout=self._timeout,
            ) as resp:
                raw_text = await resp.text()
                date_header = resp.headers.get("Date")
                if resp.status == 401:
                    raise ISolarCloudAuthError(f"HTTP 401 on {endpoint}")
                if resp.status != 200:
                    raise ISolarCloudConnectionError(f"HTTP {resp.status} on {endpoint}")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ISolarCloudConnectionError(f"Network error on {endpoint}: {err}") from err

        parsed = self._decode_response(raw_text, aes_key)
        result_code = str(parsed.get("result_code") or "")
        result_msg = str(parsed.get("result_msg") or "")

        if "expired request" in result_msg.lower() and retry_clock:
            self._update_clock_offset(date_header)
            return await self._post_encrypted(
                base_url=base_url,
                endpoint=endpoint,
                data=data,
                include_auth=include_auth,
                retry_clock=False,
            )

        if result_code == "1" and result_msg.lower() in ("", "success"):
            return parsed

        lower_msg = result_msg.lower()
        if result_code in _TOKEN_INVALID_CODES or any(m in lower_msg for m in _TOKEN_INVALID_MSGS):
            raise ISolarCloudAuthError(f"Session invalid ({result_code}): {result_msg}")
        if any(m in lower_msg for m in _AUTH_FAILED_MSGS):
            raise ISolarCloudAuthError(f"Authentication failed ({result_code}): {result_msg}")

        raise ISolarCloudApiError(f"API error on {endpoint} ({result_code}): {result_msg}")

    def _decode_response(self, raw_text: str, aes_key: str) -> dict[str, Any]:
        stripped = raw_text.strip()
        if not stripped:
            raise ISolarCloudApiError("Empty response body from iSolarCloud")
        try:
            decrypted = aes_decrypt_hex(stripped, aes_key)
            data = json.loads(decrypted)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        try:
            data = json.loads(stripped)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError as err:
            raise ISolarCloudApiError(f"Invalid JSON response: {err}") from err
        raise ISolarCloudApiError("Unexpected response payload structure")

    def _update_clock_offset(self, date_header: str | None) -> None:
        if not date_header:
            return
        try:
            server_dt = parsedate_to_datetime(date_header)
            if server_dt.tzinfo is None:
                server_dt = server_dt.replace(tzinfo=UTC)
            self._clock_offset_seconds = server_dt.timestamp() - datetime.now(UTC).timestamp()
        except Exception:
            pass
