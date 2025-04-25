
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

    description: str
    code: Type

    def __str__(self):
        return f"{self.code}: {self.description}"
