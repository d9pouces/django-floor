import logging
from socket import error as socket_error

from django.http import BadHeaderError

__author__ = "Matthieu Gallet"
logger = logging.getLogger("django.request")


# noinspection PyClassHasNoInit
class WebSocketError(socket_error):
    """
    Raised when an active websocket encounters a problem.
    """


class NoWindowKeyException(ValueError):
    """raise when the middleware DjangoFloorMiddleware is not used."""


# noinspection PyClassHasNoInit
class FrameTooLargeException(WebSocketError):
    """
    Raised if a received frame is too large.
    """


class HandshakeError(BadHeaderError):
    """
    Raised if an error occurs during protocol handshake.
    """


class UpgradeRequiredError(HandshakeError):
    """
    Raised if protocol must be upgraded.
    """
