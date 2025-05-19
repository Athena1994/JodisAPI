from pathlib import Path
import tempfile
from services.jobs.job_data import JobData
from services.server_modules.utils.js_component_provider \
    import JSComponentProvider
from services.server_modules.utils.module_fs_control import ModuleFSControl
from services.server_modules.utils.module_identifier import ModuleIdentifier
from services.server_modules.utils.py_module_provider \
    import PyModuleProvider
from services.server_modules.utils.web_component import WebComponent
from services.jobs.job_provider import JobProvider
from services.static_file_service import StaticFileService
from utils.injector import inject

PAYLOAD_DIR = 'payload'


class ModuleJobProvider(JobProvider):
    def __init__(self, module_id: ModuleIdentifier, sub_id: int,
                 cp: JSComponentProvider,
                 mp: PyModuleProvider,
                 fs: ModuleFSControl):
        super().__init__(module_id)

        self._sub_id = sub_id
        self._cp = cp
        self._mp = mp
        self._fs = fs

        self._client_url = None
        self._client_hash = None

        self._payload_dir = Path(self._fs.runtime_path, PAYLOAD_DIR)
        if not self._payload_dir.exists():
            self._payload_dir.mkdir(parents=True)

    # --- properties ---

    @property
    def client_module_url(self) -> str:
        if self._client_url is None:
            raise ValueError("Client module URL not set.")
        return self._client_url

    @client_module_url.setter
    def client_module_url(self, url: str) -> None:
        self._client_url = url

    @property
    def client_hash(self) -> str:
        if self._client_hash is None:
            raise ValueError("Client module hash not set.")
        return self._client_hash

    @client_hash.setter
    def client_hash(self, hash: str) -> None:
        self._client_hash = hash

    @property
    def src_hash(self):
        return self.client_hash

    @property
    def client_url(self):
        return self.client_module_url

    @property
    def config_component(self) -> WebComponent:
        return self._cp.get_component(self._sub_id, 'config-component')

    # --- public methods ---

    def create_job(self, cfg):

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            self.prepare_job(cfg, tmp_dir)
            archive_name = str(
                self._fs.create_archive(tmp_dir, PAYLOAD_DIR).name)

        return JobData(
            module_id=str(self.id),
            cfg=cfg,
            payload_key=archive_name)

    @inject
    def serve_payload_files(self, sfs: StaticFileService):
        """
        Serve the payload files to the client.
        """
        if not self._payload_dir.exists():
            raise FileNotFoundError("Payload directory does not exist.")

        for file in self._payload_dir.rglob('*'):
            if file.is_file():
                sfs.add_file(file, file.name)

    # --- abstract methods ---

    def prepare_job(self, cfg: dict, target_path: Path) -> None:
        raise NotImplementedError()

    def validate_config(self, cfg: dict) -> bool:
        raise NotImplementedError()
