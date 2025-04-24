

from dataclasses import dataclass
from pathlib import Path

from utils import hash_utils


class ModuleFSControl:
    @dataclass
    class Config:
        src_path: str

        @staticmethod
        def from_json(cfg: dict):
            if 'src_path' not in cfg:
                raise KeyError("Key 'src_path' not found in configuration.")
            return ModuleFSControl.Config(src_path=cfg['src_path'])

    def __init__(self, base_path: str, cfg: Config):
        self._base_path = Path(base_path)
        self._src_path = self._base_path.joinpath(cfg.src_path)

    def is_valid(self) -> bool:
        return self._src_path.exists() and self._src_path.is_dir()

    def get_src_path(self) -> Path:
        """
        Returns the source path of the module.
        """
        return self._src_path

    def get_src_hash(self) -> str:
        """
        Returns the hash of the source path.
        """
        return hash_utils.hash_dir(self._src_path).hexdigest()
