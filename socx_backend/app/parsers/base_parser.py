"""
Base parser interface (Strategy pattern) and a registry that maps
LogSourceType -> parser class, so the parsing service never needs an
if/elif chain and new sources are added by writing one new file.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from app.models.log import LogSourceType
from app.parsers.schema import ParseResult


class ParserError(Exception):
    """
    Raised for a whole-file failure the parser cannot recover from at all
    (e.g. the file can't be opened, or isn't the claimed format at a
    structural level). Per-record malformed data should NOT raise this —
    it should be counted in ParseStats.failed instead, so one bad line
    doesn't abort an otherwise-good file.
    """


class BaseParser(ABC):
    """Every concrete parser implements `parse(file_path) -> ParseResult`."""

    source_type: ClassVar[LogSourceType]

    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """
        Parses the file at `file_path` and returns every entry it could
        extract plus statistics on the run. Must not raise for per-record
        issues — only for whole-file failures (see ParserError).
        """
        raise NotImplementedError


class ParserRegistry:
    _registry: dict[LogSourceType, type[BaseParser]] = {}

    @classmethod
    def register(cls, parser_cls: type[BaseParser]) -> type[BaseParser]:
        cls._registry[parser_cls.source_type] = parser_cls
        return parser_cls

    @classmethod
    def get_parser(cls, source_type: LogSourceType) -> BaseParser:
        parser_cls = cls._registry.get(source_type)
        if parser_cls is None:
            raise ParserError(f"No parser registered for source type '{source_type.value}'")
        return parser_cls()

    @classmethod
    def supported_source_types(cls) -> set[LogSourceType]:
        return set(cls._registry.keys())
