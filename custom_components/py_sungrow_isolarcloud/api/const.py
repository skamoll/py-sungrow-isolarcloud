"""Constants for the iSolarCloud wire protocol and endpoints."""

from __future__ import annotations

GATEWAY_AUTO = "auto"

GATEWAYS: dict[str, str] = {
    "eu": "https://gateway.isolarcloud.eu",
    "com": "https://gateway.isolarcloud.com",
    "au": "https://augateway.isolarcloud.com",
    "hk": "https://gateway.isolarcloud.com.hk",
    "cn": "https://gateway.isolarcloud.com.cn",
    "in": "https://gateway.isolarcloud.in",
}

AUTO_GATEWAY_ORDER: tuple[str, ...] = (
    "https://gateway.isolarcloud.eu",
    "https://gateway.isolarcloud.com",
    "https://augateway.isolarcloud.com",
    "https://gateway.isolarcloud.com.hk",
    "https://gateway.isolarcloud.com.cn",
    "https://gateway.isolarcloud.in",
)

DEFAULT_APP_KEY = "B0455FBE7AA0328DB57B59AA729F05D8"
DEFAULT_ACCESS_KEY = "9grzgbmxdsp3arfmmgq347xjbza4ysps"
DEFAULT_WEB_VERSION = "2026011301"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
)

RSA_PUBLIC_KEY_B64URL = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCkecphb6vgsBx4LJknKKes-eyj"
    "7-RKQ3fikF5B67EObZ3t4moFZyMGuuJPiadYdaxvRqtxyblIlVM7omAasROtKRht"
    "gKwwRxo2a6878qBhTgUVlsqugpI_7ZC9RmO2Rpmr8WzDeAapGANfHN5bVr7G7GYG"
    "wIrjvyxMrAVit_oM4wIDAQAB"
)

ENDPOINT_LOGIN = "/v1/userService/login"
ENDPOINT_GET_PS_LIST = "/v1/powerStationService/getPsList"
ENDPOINT_GET_PS_DETAIL_WITH_PS_TYPE = "/v1/powerStationService/getPsDetailWithPsType"
ENDPOINT_GET_PS_ALL_DEVICE_LIST = "/v1/devService/getPsAllDeviceList"
ENDPOINT_GET_DEVICE_POINTS = "/v1/devService/getDevicePoints"
