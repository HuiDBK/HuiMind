"""Buddy managers."""

from src.dao.orm.manager.base import BaseManager
from src.dao.orm.table import BuddyProfileTable


class BuddyProfileManager(BaseManager):
    orm_table = BuddyProfileTable
