from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "MedRAG Copilot"
    database_url: str = ""
    vector_db_path: str = "./data/vector_store"
    llm_model_path: str = ""
    ncbi_api_key: str = ""
    wandb_api_key: str = ""


settings = Settings()
