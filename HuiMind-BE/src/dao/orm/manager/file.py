"""File managers."""

from src.dao.orm.manager.base import BaseManager
from src.dao.orm.table import FileTable


class FileManager(BaseManager):
    orm_table = FileTable

