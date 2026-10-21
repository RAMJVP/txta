from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = 'development'
    navigator_allowed_origins: str = 'https://inspireme.in,http://localhost:5173'
    mongodb_uri: str = ''
    mongodb_database: str = 'inspireme'
    atlas_lexical_index: str = 'kb_lexical_v1'
    atlas_vector_index: str = 'kb_vector_v1'
    embedding_provider: str = 'local'
    embedding_model: str = 'intfloat/multilingual-e5-small'
    embedding_fallback_model: str = 'sentence-transformers/all-MiniLM-L6-v2'
    embedding_dimension: int = 384
    navigator_result_limit: int = 2
    navigator_candidate_limit: int = 10
    navigator_session_max_turns: int = 5
    navigator_session_ttl_minutes: int = 30
    navigator_query_max_length: int = 300
    navigator_request_timeout_ms: int = 5000
    navigator_body_max_bytes: int = 4096
    navigator_log_retention_days: int = 30
    navigator_rate_limit_per_minute: int = 30
    navigator_min_rrf_score: float = 0.014
    navigator_high_rrf_score: float = 0.027
    navigator_min_vector_score: float = 0.55
    navigator_embedding_cache_size: int = 1000
    navigator_search_cache_ttl_seconds: int = 60
    admin_reindex_token: str = ''
    navigator_sitemap_url: str = 'https://inspireme.in/sitemap.xml'
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    @property
    def allowed_origins(self): return [x.strip() for x in self.navigator_allowed_origins.split(',') if x.strip()]

@lru_cache
def get_settings(): return Settings()
