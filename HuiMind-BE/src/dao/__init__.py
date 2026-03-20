from src import settings
from src.dao.redis import RedisManager

from py_tools.connections.db.mysql import DBManager, SQLAlchemyManager
from py_tools.connections.db.mysql.orm_model import BaseOrmTable


async def init_orm():
    """初始化mysql的ORM"""
    db_client = SQLAlchemyManager(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        db_name=settings.mysql_dbname,
    )
    db_client.init_mysql_engine()
    DBManager.init_db_client(db_client)
    return db_client


async def init_orm_tables(db_client: SQLAlchemyManager):
    """初始化 ORM 表结构"""
    from src.dao.orm import table  # noqa: F401

    async with db_client.db_engine.begin() as conn:
        await conn.run_sync(BaseOrmTable.metadata.create_all)


async def init_redis():
    RedisManager.init_redis_client(
        async_client=True,
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        db=settings.redis_db,
    )
