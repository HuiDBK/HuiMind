import os

server_host = os.getenv("SERVER_HOST", "127.0.0.1")
server_port = int(os.getenv("SERVER_PORT", "8000"))
server_log_level = os.getenv("SERVER_LOG_LEVEL", "info")

openai_api_key = os.getenv("OPENAI_API_KEY", "")
openai_api_base = os.getenv("OPENAI_API_BASE", "https://zapi.aicc0.com/")
model_name = os.getenv("MODEL_NAME", "gpt-5.4")
embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
file_storage_dir = os.getenv("FILE_STORAGE_DIR", "./uploads")


def _normalize_openai_base_url(raw: str) -> str:
    base = (raw or "").rstrip("/")
    if not base:
        return ""
    if base.endswith("/v1"):
        return base
    return base + "/v1"


openai_base_url = _normalize_openai_base_url(openai_api_base)
