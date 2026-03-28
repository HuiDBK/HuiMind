from enum import Enum

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

from src import settings


class LLMProvider(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    CLAUDE = "claude"
    OLLAMA = "ollama"


class LLMConfig:
    def __init__(
        self,
        *,
        model_name: str | None = None,
        temperature: float = 0.3,
        streaming: bool = True,
        max_tokens: int | None = None,
        timeout: int | None = None,
    ):
        self.model_name = model_name or settings.model_name
        self.temperature = temperature
        self.streaming = streaming
        self.max_tokens = max_tokens
        self.timeout = timeout


# 只给“OpenAI兼容”用
_OPENAI_COMPATIBLE = {
    LLMProvider.OPENAI: {
        "base_url": settings.openai_base_url,
        "api_key": settings.openai_api_key,
    },
    LLMProvider.DEEPSEEK: {
        "base_url": "https://api.deepseek.com/v1",
        "api_key": settings.openai_api_key,
    },
    LLMProvider.QWEN: {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": settings.openai_api_key,
    },
}


class LLMService:
    _cache: dict[str, BaseChatModel] = {}

    @classmethod
    def get(
        cls,
        provider: LLMProvider = LLMProvider.OPENAI,
        config: LLMConfig | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        use_cache: bool = True,
    ) -> BaseChatModel:
        config = config or LLMConfig()

        cache_key = f"{provider}:{config.__dict__}"

        if use_cache and cache_key in cls._cache:
            return cls._cache[cache_key]

        # ========================
        # 1️⃣ OpenAI-compatible
        # ========================
        if provider in _OPENAI_COMPATIBLE:
            conf = _OPENAI_COMPATIBLE[provider]

            llm = ChatOpenAI(
                openai_api_key=api_key or conf["api_key"],
                base_url=base_url or conf["base_url"],
                model_name=config.model_name,
                temperature=config.temperature,
                streaming=config.streaming,
                max_tokens=config.max_tokens,
                timeout=config.timeout,
            )

        # ========================
        # 2️⃣ Claude
        # ========================
        elif provider == LLMProvider.CLAUDE:
            llm = ChatAnthropic(
                anthropic_api_key=api_key or settings.anthropic_api_key,
                model=config.model_name or "claude-3-opus-20240229",
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout,
            )

        # ========================
        # 3️⃣ Ollama
        # ========================
        elif provider == LLMProvider.OLLAMA:
            llm = ChatOllama(
                base_url=base_url or "http://localhost:11434",
                model=config.model_name or "llama3",
                temperature=config.temperature,
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        if use_cache:
            cls._cache[cache_key] = llm

        return llm

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()