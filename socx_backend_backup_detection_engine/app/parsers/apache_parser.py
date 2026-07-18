"""
Parser for Apache access logs (Combined Log Format).
"""
from __future__ import annotations

from app.models.log import LogSourceType
from app.parsers.base_parser import ParserRegistry
from app.parsers.common_log_format import CommonLogFormatParser


@ParserRegistry.register
class ApacheParser(CommonLogFormatParser):
    source_type = LogSourceType.APACHE
