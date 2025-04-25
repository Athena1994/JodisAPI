

from dataclasses import dataclass
from pathlib import Path

from utils import hash_utils


class ModuleFSControl:
    @dataclass
    class Config:
        src_path: str
        module_file: str

        @staticmethod
        def from_json(cfg: dict):
            if 'distribution' not in cfg:
                raise KeyError("Key 'distribution' not found in configuration.")
            if 'module-file' not in cfg:
                raise KeyError("Key 'module-file' not found in configuration.")
            return ModuleFSControl.Config(
                src_path=cfg['distribution'],
                module_file=cfg['module-file'])

    def __init__(self, base_path: str, cfg: Config):
        self._base_path = Path(base_path)
        self._src_path = self._base_path.joinpath(cfg.src_path)
        self._module_file = self._base_path.joinpath(cfg.module_file)

        self._last_hash = None

    def is_valid(self) -> bool:
        return (self._src_path.exists() and self._src_path.is_dir()
                and self._module_file.exists())

    def get_src_path(self) -> Path:
        """
        Returns the source path of the module.
        """
        return self._src_path

    def has_changed(self) -> bool:
        """
        Returns True if the source path has changed since the last hash
        calculation.
        """
        prev_hash = self._last_hash
        return self.calc_hash(False) != prev_hash

    def calc_hash(self, update_last_hash: bool = True) -> str:
        """
        Returns the hash of the source path.
        """
        if self.is_valid():
            current_hash = hash_utils.hash_dir(self._src_path)
            current_hash.update(hash_utils.hash_file(self._module_file))
        else:
            current_hash = ""

        if update_last_hash:
            self._last_hash = current_hash

        return current_hash

    def get_last_hash(self) -> str:
        """
        Returns the last hash of the source path.
        """
        return self._last_hash
