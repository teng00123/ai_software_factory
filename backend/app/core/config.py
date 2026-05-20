from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    # 应用配置
    DEBUG: bool = Field(default=False, description="调试模式")
    HOST: str = Field(default="0.0.0.0", description="监听主机")
    PORT: int = Field(default=8000, description="监听端口")

    # API配置
    API_V1_STR: str = Field(default="/api/v1", description="API版本前缀")

    # JWT配置
    SECRET_KEY: str = Field(
        default="change-this-to-a-random-string-in-production",
        description="JWT签名密钥"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24,  # 24 hours
        description="Token过期时间（分钟）"
    )

    # 数据库配置
    DATABASE_URL: str = Field(
        default="mysql+aiomysql://root:changeme@127.0.0.1:3306/ai_software_factory",
        description="数据库连接字符串"
    )

    # CORS配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="允许的跨域源"
    )

    # LLM配置
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API Key")
    LLM_MODEL: str = Field(
        default="claude-sonnet-4-20250514",
        description="默认 LLM 模型"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()