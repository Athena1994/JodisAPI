import logging
from pathlib import Path
import tempfile
import zipfile
from injector import inject

from services.jobs.job_service import JobService
from services.server_modules.sub_modules.job_module.module_job_provider \
    import ModuleJobProvider
from services.server_modules.sub_modules.sub_module import SubModule
from services.server_modules.sub_modules.sub_module_types \
    import SubModuleTypes
from services.server_modules.utils.js_component_provider \
    import JSComponentProvider
from services.server_modules.utils.module_fs_control import ModuleFSControl
from services.server_modules.utils.py_component import PyComponent
from services.server_modules.utils.py_module_provider \
    import PyModuleProvider
from services.server_modules.utils.module_identifier import ModuleIdentifier
from services.server_modules.utils.web_component import WebComponent
from services.static_file_service import StaticFileService

from jodisutils.files import hash_utils
from jodisutils.config.decorator import config
from jodisutils.config.attribute import Attribute


class JobSubModule(SubModule):

    @config
    class Config:
        config_component: WebComponent = Attribute(
            json_field='config-component',
            deserializer=lambda x: (
                {'module': x, 'class': x} if isinstance(x, str) else x),
            required=True
        )
        job_provider: PyComponent = Attribute('job-provider', required=True)

        client_module: Path = Attribute(
            'client-module', required=True, json_type=str,)

    @inject
    def __init__(self,
                 module_id: ModuleIdentifier, sub_id: int,

                 cp: JSComponentProvider, mp: PyModuleProvider,
                 fs: ModuleFSControl,

                 cfg: Config):
        super().__init__(
            module_id=module_id, sub_id=sub_id,
            type=SubModuleTypes.JOB_MODULE,
            cp=cp, mp=mp)

        self._client_file_id = None
        self._client_module_path = fs.get_src_path().joinpath(cfg.client_module)

        self._tmp_dir = None

        cp.register_component(
            sub_id,
            cfg.config_component.module_url,
            cfg.config_component.component_class,
            'config-component')

        mp.register_module(cfg.job_provider.file, 'job-provider-module')

        mp.register_class(
            'job-provider-module',
            cfg.job_provider.class_name,
            "job-provider")

        self._job_provider: ModuleJobProvider = \
            mp.create_class("job-provider", module_id, sub_id, cp, mp, fs)

        self._job_provider.client_hash = hash_utils.hash_dir(
            self._client_module_path.joinpath('src')).hexdigest()

    @inject
    def start(self, js: JobService, sfs: StaticFileService):
        logging.debug("Starting job submodule %s", self.module_id)
        js.register_provider(self.module_id, self._job_provider)

        self._tmp_dir = tempfile.TemporaryDirectory()

        # serve client module as zip file
        zip_path = Path(self._tmp_dir.name) / "client.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in self._client_module_path.rglob('*'):
                zipf.write(file, file.relative_to(self._client_module_path))
        self._client_file_id = sfs.add_file(zip_path)

        self._job_provider.client_module_url \
            = sfs.get_file_url(self._client_file_id)

        # serve payload files
        self._job_provider.serve_payload_files()

    @inject
    def stop(self, js: JobService, sfs: StaticFileService):
        js.unregister_provider(self.module_id)
        sfs.remove_file(self._client_file_id)
        self._tmp_dir.cleanup()

    def is_busy(self):
        return False
