from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Backblaze B2 (S3-compatible API) — Standard #3 env names. No region
    # string is hardcoded; the endpoint and region both come from .env.
    b2_endpoint: str = ""
    b2_application_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = ""
    # Passed straight through to boto3 as region_name. No region string is
    # hardcoded anywhere in source — it always comes from here.
    b2_region: str = ""
    b2_public_url: str = ""

    # OpenAI — powers BOTH script generation (LLM) and audio synthesis (TTS).
    # A single key and SDK covers both; see repo/llm_client.py + repo/tts_client.py.
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    tts_model: str = "gpt-4o-mini-tts"
    # Two-host podcast: each host gets a distinct OpenAI voice + display name.
    tts_voice_host_a: str = "alloy"
    tts_voice_host_b: str = "verse"
    host_a_name: str = "Alex"
    host_b_name: str = "Sam"

    api_port: int = 8000
    # Explicit allowlist by default — covers Next on :3000 and the
    # fallback :3001 it picks if 3000 is busy. Production deploys should
    # override with the exact frontend origin.
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    # Optional dev-only escape hatch: a regex that matches additional
    # allowed origins. Empty by default — set this to e.g.
    # `^http://localhost:\d+$` to accept any localhost port without
    # listing each one. NEVER ship this to production.
    api_cors_origin_regex: str = ""

    # Upload limits
    max_file_size: int = 100 * 1024 * 1024  # 100MB

    # Small durable counters (downloads, etc). Point at a persistent
    # volume in production if you care about surviving restarts.
    download_count_file: str = "data/download_count.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]


settings = Settings()
