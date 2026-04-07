from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src import settings
from src.dao.redis import RedisManager

from py_tools.connections.db.mysql import DBManager, SQLAlchemyManager
from py_tools.connections.db.mysql.orm_model import BaseOrmTable


async def init_orm():
    """初始化sqlite的ORM (模拟 mysql)"""
    # 使用 sqlite+aiosqlite 模拟
    db_url = f"sqlite+aiosqlite:///{settings.mysql_dbname}.db"
    logger.info(f"Initializing SQLite ORM at {db_url}")

    # 构造一个兼容 SQLAlchemyManager 的对象，满足 DBManager.init_db_client 的要求
    class SQLiteManager:
        def __init__(self, engine, session_maker):
            self.db_engine = engine
            self.async_session_maker = session_maker
            self.session_options = {"expire_on_commit": False}

    engine = create_async_engine(db_url, echo=True)
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

    db_client = SQLiteManager(engine, session_maker)
    DBManager.init_db_client(db_client)
    return db_client


async def init_orm_tables(db_client):
    """初始化 ORM 表结构"""
    from src.dao.orm import table  # noqa: F401

    async with db_client.db_engine.begin() as conn:
        # 说明：
        # 当前 MVP 使用 sqlite+create_all 方式初始化表结构，没有迁移系统。
        # 在开发/未上线阶段，允许 drop_all -> create_all 以适配表结构调整（如新增/删除列）。
        await conn.run_sync(BaseOrmTable.metadata.drop_all)
        await conn.run_sync(BaseOrmTable.metadata.create_all)


async def init_redis():
    try:
        RedisManager.init_redis_client(
            async_client=True,
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
        )
    except Exception as exc:
        logger.warning("Redis init skipped: %s", exc)
