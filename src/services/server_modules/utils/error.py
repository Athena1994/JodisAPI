
from dataclasses import dataclass
import enum


@dataclass
class Error:
    class Type(enum.Enum):
        PATH_NOT_FOUND = "path_not_found"
        CFG_INVALID = "config_invalid"
        INITIALIZATION_FAILED = "initialization_failed"
        UNKNOWN = "unkown",
        FILE_STRUCTURE_INVALID = "file_structure_invalid"
        INTERNAL_ERROR = "internal_error"

    description: str
    code: Type
    traceback: str = None

    def __str__(self):
        if self.traceback:
            return f"{self.code}: {self.description}\n{self.traceback}"
        return f"{self.code}: {self.description}"
