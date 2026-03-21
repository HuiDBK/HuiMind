# mysql服务配置
mysql_host = "127.0.0.1"
mysql_port = 3306
mysql_user = "root"
mysql_password = "123456"
mysql_dbname = "task_flow"


# redis服务配置
redis_host = "127.0.0.1"
redis_port = 6379
redis_password = ""
redis_db = 0

# celery配置
celery_broker_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
celery_result_backend = f"redis://{redis_host}:{redis_port}/{redis_db}"
