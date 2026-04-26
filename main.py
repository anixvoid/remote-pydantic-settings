from remote_pydantic_settings import RemoteSettings
from pydantic import Field

class Settings(RemoteSettings):
    log_level: str = Field('INFO', validation_alias='LOG_LEVEL')
    db_user: str = Field('', validation_alias='DB_USER')
    db_pass: str = Field('', validation_alias='DB_PASS')
    api_key: str = Field('', validation_alias='API_KEY')

    model_config = {'env_file': '.env', 'extra': 'ignore'}

settings = Settings()

print(settings.db_user)   # значение из JSON в Redis
print(settings.api_key)   # access_token из JSON-ответа HTTP