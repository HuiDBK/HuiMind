"""Document managers."""

from src.dao.orm.manager.base import BaseManager
from src.dao.orm.table import DocumentTable


class DocumentManager(BaseManager):
    orm_table = DocumentTable
