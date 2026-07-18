"""
Importing this package registers every concrete parser with
ParserRegistry (each module below decorates its class with
@ParserRegistry.register on import). Anything that needs to resolve a
parser by source type — the parsing service, tests, etc. — should import
`app.parsers` (or any of these submodules) before calling
ParserRegistry.get_parser().
"""
from app.parsers.base_parser import BaseParser, ParserError, ParserRegistry  # noqa: F401
from app.parsers.schema import ParsedLogEntry, ParseResult, ParseStats  # noqa: F401

from app.parsers.evtx_parser import EvtxParser  # noqa: F401
from app.parsers.linux_auth_parser import LinuxAuthParser  # noqa: F401
from app.parsers.apache_parser import ApacheParser  # noqa: F401
from app.parsers.nginx_parser import NginxParser  # noqa: F401
from app.parsers.json_parser import JsonParser  # noqa: F401
from app.parsers.csv_parser import CsvParser  # noqa: F401

__all__ = [
    "BaseParser",
    "ParserError",
    "ParserRegistry",
    "ParsedLogEntry",
    "ParseResult",
    "ParseStats",
    "EvtxParser",
    "LinuxAuthParser",
    "ApacheParser",
    "NginxParser",
    "JsonParser",
    "CsvParser",
]
