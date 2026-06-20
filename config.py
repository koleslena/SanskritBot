from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_URL: str
    SANSBOT_TOKEN: str

    model_config = SettingsConfigDict(
        extra="ignore" # игнорируем переменные для API, если они попадут сюда
    )

settings = Settings()