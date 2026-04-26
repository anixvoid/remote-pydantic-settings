# test_settings.py
from pydantic import Field
from remote_pydantic_settings import RemoteSettings
import os

# Создаём тестовый .env файл
with open('.env', 'w') as f:
    f.write("""
LOG_LEVEL=DEBUG
DB_HOST=redis://localhost:6379/0?key=test_db_host
API_URL=https://httpbin.org/get?json_key=origin
PLAIN_VALUE=hello_world
""")

class Settings(RemoteSettings):
    log_level   : str = Field('INFO',               validation_alias='LOG_LEVEL')
    db_host     : str = Field('localhost',          validation_alias='DB_HOST')
    api_url     : str = Field('http://example.com', validation_alias='API_URL')
    plain_value : str = Field('default',            validation_alias='PLAIN_VALUE')

# Тестируем
print("=== Тест RemoteSettings ===")

try:
    settings = Settings()
    print(f"log_level: {settings.log_level}")      # DEBUG
    print(f"plain_value: {settings.plain_value}")  # hello_world
    print(f"db_host: {settings.db_host}")          # значение из Redis или 'localhost' если Redis недоступен
    print(f"api_url: {settings.api_url}")          # origin из httpbin или 'http://example.com' если нет интернета
    print("✅ Тест пройден!")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Удаляем тестовый .env
    if os.path.exists('.env'):
        os.remove('.env')