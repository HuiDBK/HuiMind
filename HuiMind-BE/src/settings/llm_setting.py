"""LLM 配置模块。

该模块包含所有与 LLM（大语言模型）相关的配置项，包括：
- OpenAI API 配置
- 模型名称配置
- Embedding 模型配置
"""

import os


# OpenAI API 配置
openai_api_key = os.getenv("OPENAI_API_KEY", "sk-")
openai_api_base = os.getenv("OPENAI_API_BASE", "https://zapi.aicc0.com/v1")

# 模型配置
model_name = os.getenv("MODEL_NAME", "gpt-5.4")

# embedding 使用阿里的云百炼模型
embedding_api_base = os.getenv("EMBEDDING_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "sk-")
embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v4")
