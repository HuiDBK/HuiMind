"""RAG managers."""

from src.dao.orm.manager.base import BaseManager
from src.dao.orm.table import QaRecordTable


class QaRecordManager(BaseManager):
    orm_table = QaRecordTable
