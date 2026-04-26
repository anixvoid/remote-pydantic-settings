"""
Модуль поддержки удалённых источников конфигурации для Pydantic Settings.
Позволяет в .env указывать ссылки на Redis или HTTP(S) вместо прямых значений.
Поддерживает извлечение значений из JSON через параметры json_key и json_path.
"""
import json
import os
from urllib.parse import urlparse, parse_qs
from typing import Optional, Any

from pydantic_settings import BaseSettings


def extract_json_value(json_str: str, key: str, use_path: bool = False) -> Optional[str]:
    """Извлекает значение из JSON-строки по ключу или пути (dot-нотация)."""
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None

    if use_path:
        parts = key.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return str(current) if current is not None else None
    else:
        if isinstance(data, dict) and key in data:
            value = data[key]
            return str(value) if value is not None else None
        return None


def get_from_redis_url(url: str) -> Optional[str]:
    """Получает значение из Redis по URL."""
    try:
        import redis
    except ImportError:
        raise ImportError("Для Redis-ссылок необходим пакет 'redis'")

    parsed = urlparse(url)
    if parsed.scheme not in ('redis', 'rediss'):
        return None

    host = parsed.hostname or 'localhost'
    port = parsed.port or 6379
    password = parsed.password
    db = int(parsed.path.strip('/') or 0)
    params = parse_qs(parsed.query)

    key = params.get('key', [None])[0]
    timeout = float(params.get('timeout', [2])[0])
    json_key = params.get('json_key', [None])[0]
    json_path = params.get('json_path', [None])[0]

    if not key:
        return None

    try:
        r = redis.Redis(
            host=host, port=port, password=password, db=db,
            socket_connect_timeout=timeout, decode_responses=True,
        )
        raw_value = r.get(key)
    except Exception:
        return None

    if raw_value is None:
        return None

    if json_key:
        return extract_json_value(raw_value, json_key, use_path=False)
    elif json_path:
        return extract_json_value(raw_value, json_path, use_path=True)

    return raw_value


def get_from_http_url(url: str) -> Optional[str]:
    """Выполняет GET-запрос по HTTP(S) и возвращает тело ответа."""
    try:
        import requests
    except ImportError:
        raise ImportError("Для HTTP(S)-ссылок необходим пакет 'requests'")

    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return None
    params = parse_qs(parsed.query)
    timeout = float(params.get('timeout', [5])[0])
    json_key = params.get('json_key', [None])[0]
    json_path = params.get('json_path', [None])[0]

    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        text = resp.text.strip()
    except Exception:
        return None

    if json_key:
        return extract_json_value(text, json_key, use_path=False)
    elif json_path:
        return extract_json_value(text, json_path, use_path=True)
    else:
        return text


def _resolve_remote_value(raw: str) -> Optional[str]:
    """Если значение - удалённая ссылка, разрешает её."""
    parsed = urlparse(raw)
    if parsed.scheme in ('redis', 'rediss'):
        return get_from_redis_url(raw)
    elif parsed.scheme in ('http', 'https'):
        return get_from_http_url(raw)
    return None


class RemoteSettings(BaseSettings):
    """
    Базовый класс настроек с поддержкой удалённых источников.
    
    Пример .env:
        DB_HOST=redis://:pass@10.0.0.1:6379/0?key=prod/db/host
        API_URL=https://api.example.com/config?json_key=url
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._apply_remote_sources()

    def _apply_remote_sources(self):
        """Применяет удалённые источники для всех полей с URL-ссылками."""
        for field_name, field_info in self.model_fields.items():
            # Получаем текущее значение поля (уже загруженное Pydantic из .env или env)
            current_value = getattr(self, field_name)
            
            # Проверяем, является ли значение строкой с URL-ссылкой
            if not isinstance(current_value, str):
                continue
            
            # Пытаемся разрешить удалённую ссылку
            resolved = _resolve_remote_value(current_value)
            if resolved is not None:
                # Преобразуем тип значения в соответствии с аннотацией поля
                typed_value = self._convert_type(field_name, resolved)
                object.__setattr__(self, field_name, typed_value)

    def _convert_type(self, field_name: str, value: str) -> Any:
        """Преобразует строковое значение к нужному типу поля."""
        field_info = self.model_fields[field_name]
        field_type = field_info.annotation
        
        if field_type is bool or str(field_type) == 'bool':
            return value.lower() in ('true', '1', 'yes')
        elif field_type is int or str(field_type) == 'int':
            try:
                return int(value)
            except ValueError:
                return value
        elif field_type is float or str(field_type) == 'float':
            try:
                return float(value)
            except ValueError:
                return value
        
        return value