
from enum import Enum


class TaskStatus(str, Enum):
    WAITING = "waiting"
    PENDING = "pending"
    DONE = "done"
    ERROR = "error"
    CANCEL = "cancel"
