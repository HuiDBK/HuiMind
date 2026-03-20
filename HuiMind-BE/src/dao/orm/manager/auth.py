"""Auth managers."""

from src.dao.orm.manager.base import BaseManager
from src.dao.orm.table import UserTable


class UserManager(BaseManager):
    orm_table = UserTable
