"""Review managers."""

from src.dao.orm.manager.base import BaseManager
from src.dao.orm.table import ReviewTaskTable, WeakPointTable


class WeakPointManager(BaseManager):
    orm_table = WeakPointTable


class ReviewTaskManager(BaseManager):
    orm_table = ReviewTaskTable
