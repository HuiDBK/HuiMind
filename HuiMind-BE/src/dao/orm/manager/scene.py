"""Scene managers."""

from src.dao.orm.manager.base import BaseManager
from src.dao.orm.table import SceneTable


class SceneManager(BaseManager):
    orm_table = SceneTable
