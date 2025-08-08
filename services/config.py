"""
Production Configuration Management
Provides environment-based configuration with secure secret handling
"""

import os
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./app.db"))
    pool_size: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "10")))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_TIMEOUT", "30")))
    echo: bool = field(default_factory=lambda: os.getenv("DATABASE_ECHO", "false").lower() == "true")
    
    def __post_init__(self):
        # Validate database URL
        if not self.url:
            raise ValueError("DATABASE_URL is required")


@dataclass
class RedisConfig:
    """Redis configuration settings."""
    url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    max_connections: int = field(default_factory=lambda: int(os.getenv("REDIS_MAX_CONNECTIONS", "20")))
    socket_timeout: int = field(default_factory=lambda: int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")))
    retry_on_timeout: bool = field(default_factory=lambda: os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true")
    health_check_interval: int = field(default_factory=lambda: int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30")))


@dataclass
class ObservabilityConfig:
    """Observability and monitoring configuration."""
    otel_endpoint: str = field(default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""))
    service_name: str = field(default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "agentic-research-engine"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    enable_tracing: bool = field(default_factory=lambda: os.getenv("ENABLE_TRACING", "true").lower() == "true")
    enable_metrics: bool = field(default_factory=lambda: os.getenv("ENABLE_METRICS", "true").lower() == "true")
    
    def __post_init__(self):
        # Set up logging
        logging.basicConfig(level=getattr(logging, self.log_level.upper()))


@dataclass
class SecurityConfig:
    """Security and authentication configuration."""
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    api_keys: Dict[str, str] = field(default_factory=dict)
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_expiration: int = field(default_factory=lambda: int(os.getenv("JWT_EXPIRATION_MINUTES", "60")))
    enable_cors: bool = field(default_factory=lambda: os.getenv("ENABLE_CORS", "false").lower() == "true")
    cors_origins: list = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [])
    
    def __post_init__(self):
        # Parse API keys from environment
        raw_keys = os.getenv("API_KEYS", "")
        if raw_keys:
            for pair in raw_keys.split(","):
                if ":" in pair:
                    role, token = pair.split(":", 1)
                    self.api_keys[token.strip()] = role.strip()
        
        # Validate secret key in production
        if self.environment == "production" and not self.secret_key:
            raise ValueError("SECRET_KEY is required in production environment")


@dataclass
class ServiceConfig:
    """Service-specific configuration."""
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    workers: int = field(default_factory=lambda: int(os.getenv("WORKER_COUNT", "4")))
    max_request_size: int = field(default_factory=lambda: int(os.getenv("MAX_REQUEST_SIZE", "16777216")))  # 16MB
    request_timeout: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30")))
    graceful_shutdown_timeout: int = field(default_factory=lambda: int(os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", "30")))
    
    # Health check settings
    health_check_timeout: int = field(default_factory=lambda: int(os.getenv("HEALTH_CHECK_TIMEOUT", "5")))
    readiness_timeout: int = field(default_factory=lambda: int(os.getenv("READINESS_TIMEOUT", "10")))
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = field(default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")))
    circuit_breaker_recovery_timeout: int = field(default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30")))
    
    # Retry settings
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    retry_backoff_multiplier: float = field(default_factory=lambda: float(os.getenv("RETRY_BACKOFF_MULTIPLIER", "1.5")))


@dataclass
class StorageConfig:
    """Storage configuration settings."""
    backend: str = field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "file"))
    file_data_dir: str = field(default_factory=lambda: os.getenv("STORAGE_FILE_DIR", "./data"))
    redis_key_prefix: str = field(default_factory=lambda: os.getenv("STORAGE_REDIS_PREFIX", "episodic_memory"))
    postgres_table_name: str = field(default_factory=lambda: os.getenv("STORAGE_POSTGRES_TABLE", "episodic_memory"))
    
    # Vector store settings
    vector_store_type: str = field(default_factory=lambda: os.getenv("VECTOR_STORE_TYPE", "weaviate"))
    weaviate_url: str = field(default_factory=lambda: os.getenv("WEAVIATE_URL", "http://localhost:8080"))
    embedding_cache_size: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_CACHE_SIZE", "1000")))


@dataclass
class AppConfig:
    """Main application configuration."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    service: ServiceConfig = field(default_factory=ServiceConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    
    # Global settings
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    version: str = field(default_factory=lambda: os.getenv("SERVICE_VERSION", "1.0.0"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    def __post_init__(self):
        # Validate environment-specific settings
        if self.environment == "production":
            self._validate_production_config()
        
        # Set up logging
        log_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _validate_production_config(self):
        """Validate production-specific configuration requirements."""
        required_vars = [
            ("DATABASE_URL", self.database.url),
            ("SECRET_KEY", self.security.secret_key),
        ]
        
        missing_vars = [name for name, value in required_vars if not value]
        if missing_vars:
            raise ValueError(f"Missing required production environment variables: {missing_vars}")
        
        # Validate database URL is not using SQLite in production
        if "sqlite" in self.database.url.lower():
            logging.warning("Using SQLite in production is not recommended")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        config_dict = {}
        
        # Safe fields to expose
        safe_fields = [
            "environment", "version", "debug",
            "service.host", "service.port", "service.workers",
            "observability.service_name", "observability.environment", "observability.log_level",
            "storage.backend", "storage.vector_store_type"
        ]
        
        for field_path in safe_fields:
            try:
                obj = self
                for part in field_path.split("."):
                    obj = getattr(obj, part)
                config_dict[field_path] = obj
            except AttributeError:
                continue
        
        return config_dict


class ConfigManager:
    """Centralized configuration manager."""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def config(self) -> AppConfig:
        """Get application configuration."""
        if self._config is None:
            self._config = AppConfig()
        return self._config
    
    def reload(self) -> AppConfig:
        """Reload configuration from environment."""
        self._config = AppConfig()
        return self._config
    
    def get_database_url(self, service_name: Optional[str] = None) -> str:
        """Get database URL for specific service."""
        if service_name:
            service_url = os.getenv(f"{service_name.upper()}_DATABASE_URL")
            if service_url:
                return service_url
        
        return self.config.database.url
    
    def get_redis_url(self, service_name: Optional[str] = None) -> str:
        """Get Redis URL for specific service."""
        if service_name:
            service_url = os.getenv(f"{service_name.upper()}_REDIS_URL")
            if service_url:
                return service_url
        
        return self.config.redis.url
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.config.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.config.environment.lower() in ["development", "dev"]


# Global configuration manager instance
config_manager = ConfigManager()

# Convenience function to get configuration
def get_config() -> AppConfig:
    """Get application configuration."""
    return config_manager.config


# Environment-specific configuration loaders
def load_config_from_file(config_path: Union[str, Path]) -> Dict[str, str]:
    """Load configuration from file (for development)."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        return {}
    
    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    
    return config


def setup_development_env():
    """Set up development environment variables."""
    dev_config = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "sqlite:///./dev.db",
        "REDIS_URL": "redis://localhost:6379/0",
        "STORAGE_BACKEND": "file",
        "ENABLE_TRACING": "true",
        "ENABLE_METRICS": "true"
    }
    
    for key, value in dev_config.items():
        if key not in os.environ:
            os.environ[key] = value


def setup_test_env():
    """Set up test environment variables."""
    test_config = {
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "LOG_LEVEL": "WARNING",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/1",
        "STORAGE_BACKEND": "memory",
        "ENABLE_TRACING": "false",
        "ENABLE_METRICS": "false"
    }
    
    for key, value in test_config.items():
        os.environ[key] = value