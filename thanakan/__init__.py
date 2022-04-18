from .services import SCBAPI, KBankAPI, SCBBaseURL
from .slip import SlipQRData

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
    from importlib_metadata import PackageNotFoundError, version


try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
