"""
remote-pydantic-settings
Удалённые источники конфигурации для Pydantic Settings.
Поддерживает Redis, HTTP/HTTPS и обычные значения.
"""

__version__ = "0.2.0"

from .main import RemoteSettings

__all__ = ["RemoteSettings"]