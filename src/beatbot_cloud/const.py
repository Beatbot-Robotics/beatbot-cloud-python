"""Beatbot cloud protocol constants."""

from typing import Final

HTTP_API_TIMEOUT: Final = 30
OAUTH2_AUTHORIZE_URL: Final = "https://oauth.beatbot.com/oauth2/authorize"
OAUTH2_TOKEN_URL: Final = "https://oauth.beatbot.com/oauth2/token"
OAUTH2_CLIENT_ID: Final = "home-assistant"
OAUTH2_SCOPE: Final = "device:info"

REGION_API_BASE_URL: Final = {
    "cn": "https://cn-iot.beatbot.com",
    "na": "https://na-iot.beatbot.com",
    "eu": "https://eu-iot.beatbot.com",
}

DEVICES_PATH: Final = "/openapi/v1/ha"
DEVICE_STATES_PATH: Final = "/openapi/v1/ha/state"
DEVICE_ACTIONS_PATH: Final = "/openapi/v1/ha"
EVENTS_PATH: Final = "/openapi/v1/ha/ws"
RESULT_SUCCESS_CODE: Final = 200

INTERFACE_WORK_MODE: Final = "select.work_mode"
