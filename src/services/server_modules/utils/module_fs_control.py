
from datetime import datetime
from pathlib import Path
import uuid
from zipfile import ZipFile
import zipfile
import os


from jodisutils.files import hash_utils
from jodisutils.config.decorator import config
from jodisutils.config.attribute import Attribute


RUNTIME_PATH = "rt/"


class ModuleFSControl:
    @config
    class Config:
        src_path: Path = Attribute(
            'distribution', default='src/', json_type=str)
        module_file: Path = Attribute(
            'module-file', default='./module.json', json_type=str)

        # @staticmethod
        # def schema() -> dict:
        #     return {
        #         'type': 'object',
        #         'properties': {
        #             'distribution': {
        #                 'type': 'string',
        #                 'description': "Path to the module source code.",
        #                 'default': 'src/'
        #             },
        #             'module-file': {
        #                 'type': 'string',
        #                 'description': "Path to the module file.",
        #                 'default': './module.json'
        #             }
        #         },
        #     }

    def __init__(self, module_path: Path, cfg: Config):
        self._module_path = module_path
        self._src_path = module_path.joinpath(cfg.src_path)
        self._module_file = module_path.joinpath(cfg.module_file)

        self._last_hash = None

    # --- Properties ---

    @property
    def runtime_path(self) -> Path:
        path = self._module_path.joinpath(RUNTIME_PATH)

        if not path.exists():
            path.mkdir(parents=False, exist_ok=True)

        return path

    @property
    def last_hash(self) -> str:
        return self._last_hash

    @property
    def is_valid(self) -> bool:
        return (self._src_path.exists() and self._src_path.is_dir()
                and self._module_file.exists())

    @property
    def has_changed(self) -> bool:
        """
        Returns True if the source path has changed since the last hash
        calculation.
        """
        prev_hash = self._last_hash
        return self.calc_hash(False) != prev_hash

    # --- Public methods ---

    def get_archive(self, name: str) -> ZipFile:
        """
        Returns the archive with the given name.
        """
        archive_path = self.runtime_path.joinpath(name)
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive {name} not found.")
        return ZipFile(archive_path, 'r')

    def create_archive(self, dir: Path, target_dir: str) -> Path:
        """
        Creates an archive from dir with an unique name at module runtime dir.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        id = uuid.uuid4()
        archive_name = f"{timestamp}:{id}.zip"
        archive_path = self.runtime_path.joinpath(target_dir, archive_name)

        if not archive_path.parent.exists():
            archive_path.parent.mkdir(parents=True, exist_ok=True)

        if archive_path.exists():
            raise FileExistsError(f"Archive {archive_name} already exists.")

        with ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for file in dir.rglob('*'):
                if file.is_file():
                    archive.write(file, file.relative_to(dir))
                else:
                    archive.mkdir(file.relative_to(dir), exist_ok=True)

        return archive_path

    def remove_archive(self, name: str) -> bool:
        """
        Removes the archive with the given name.
        """
        archive_path = self.runtime_path.joinpath(name)
        if archive_path.exists():
            archive_path.unlink()
            return True
        return False

    def get_src_path(self, rel: bool = False) -> Path:
        """
        Returns the source path of the module.
        """
        if rel:
            return self._src_path.relative_to(self._module_path)
        else:
            return self._src_path

    def calc_hash(self, update_last_hash: bool = True) -> str:
        """
        Returns the hash of the source path.
        """
        if self.is_valid():
            current_hash = hash_utils.hash_dir(self._src_path)
            hash_utils.hash_file(self._module_file, current_hash)
        else:
            current_hash = ""

        if update_last_hash:
            self._last_hash = current_hash

        return current_hash.hexdigest()

    @staticmethod
    def execute_in_module_rt(fs_getter=None):
        """
        Runs the given function in the runtime directory.
        """

        def default_fs_getter(self):
            return self._fs

        def decorator(fct):
            def wrapper(*args, **kwargs):

                if fs_getter is not None:
                    fs: ModuleFSControl = fs_getter(args[0])
                else:
                    fs: ModuleFSControl = default_fs_getter(args[0])

                if not fs.runtime_path.exists():
                    raise FileNotFoundError(
                        f"Runtime path {fs.runtime_path} not found.")

                old_cwd = os.getcwd()
                os.chdir(fs.runtime_path)
                try:
                    return fct(*args, **kwargs)
                finally:
                    os.chdir(old_cwd)

            return wrapper
        return decorator
