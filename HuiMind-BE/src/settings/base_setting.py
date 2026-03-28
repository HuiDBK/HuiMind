"""基础配置模块。

该模块包含服务器基础配置和存储配置。
"""

import os

# 服务器配置
server_host = os.getenv("SERVER_HOST", "127.0.0.1")
server_port = int(os.getenv("SERVER_PORT", "8000"))
server_log_level = os.getenv("SERVER_LOG_LEVEL", "info")

# 存储配置
chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
file_storage_dir = os.getenv("FILE_STORAGE_DIR", "./uploads")
