from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/construction_commander"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password123"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    openai_api_key: str = ""
    agent_tool_delay_ms: int = 0
    qdrant_collection: str = "construction_docs"
    docs_storage_path: str = "./docs_storage"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
