
from dataclasses import dataclass
import hashlib


@dataclass
class ModuleIdentifier:
    name: str
    version: str

    @property
    def id(self) -> int:
        return hash(self)

    def __str__(self):
        return f"{self.name}:{self.version}"

    def __hash__(self):
        return int(hashlib.sha256(str(self).encode()).hexdigest(), 16)
