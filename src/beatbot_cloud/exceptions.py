"""Exceptions raised by the Beatbot cloud client."""


class BeatbotError(Exception):
    """Base class for Beatbot client errors."""


class BeatbotAuthenticationError(BeatbotError):
    """The credentials are invalid and user authentication is required."""


class BeatbotConnectionError(BeatbotError):
    """The Beatbot cloud service could not be reached or returned bad data."""


class BeatbotEventError(BeatbotConnectionError):
    """A cloud event did not match the documented event contract."""


class BeatbotTokenRejectedError(BeatbotAuthenticationError):
    """An access token was rejected and may be refreshed once."""

    def __init__(self, access_token: str, *, handshake: bool = False) -> None:
        super().__init__("access token rejected")
        self.access_token = access_token
        self.handshake = handshake


class BeatbotConnectionReplacedError(BeatbotError):
    """The server replaced this event stream with a newer connection."""
