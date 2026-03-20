"""Career managers."""

from src.dao.orm.manager.base import BaseManager
from src.dao.orm.table import InterviewSessionTable, InterviewTurnTable, ResumeDiagnosisTable


class ResumeDiagnosisManager(BaseManager):
    orm_table = ResumeDiagnosisTable


class InterviewSessionManager(BaseManager):
    orm_table = InterviewSessionTable


class InterviewTurnManager(BaseManager):
    orm_table = InterviewTurnTable
