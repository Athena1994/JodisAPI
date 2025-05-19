
from typing import TypeVar
from injector import Injector
from app_config import AppConfig
from services.client_connection_service import ClientConnectionService
from services.client_request_service import ClientRequestService
from services.jobs.job_service import JobService
from services.server_modules.server_module_service import ServerModuleService
from services.static_file_service import StaticFileService
from services.update_event_service import UpdateEventService
from utils import injector
from utils.db.db_context import DBContext
from utils.model_managing.subject_manager import SubjectManager

from flask_injector import singleton

_services = {}


T = TypeVar('T')


def get(type: T) -> T:
    first = next(filter(lambda x: isinstance(x, type), _services.values()))
    if first is not None:
        return first
    raise ValueError(f"Service of type {type} not found.")


def get_by_name(name: str):
    return _services[name]


def init(cfg: AppConfig):
    i = injector.get_injector()

    _services['sm'] = SubjectManager()
    _services['db'] = DBContext(cfg.db)
    _services['ues'] = UpdateEventService(_services['db'], _services['sm'])
    _services['ccs'] = ClientConnectionService(_services['sm'])
    _services['crs'] = ClientRequestService(_services['ccs'])
    _services['ms'] = ServerModuleService(_services['sm'])
    _services['js'] = JobService(_services['db'])
    _services['sfs'] \
        = StaticFileService(f"{cfg.server.host}:{cfg.server.port}", 'statics')

    for name, service in _services.items():
        i.bind(service.__class__, to=service)


def flask_injector_configure(binder):
    binder.bind(DBContext, to=get_by_name('db'), scope=singleton)
    binder.bind(ClientConnectionService, to=get_by_name('ccs'), scope=singleton)
    binder.bind(ClientRequestService, to=get_by_name('crs'), scope=singleton)
    binder.bind(SubjectManager, to=get_by_name('sm'), scope=singleton)
    binder.bind(ServerModuleService, to=get_by_name('ms'), scope=singleton)
    binder.bind(JobService, to=get_by_name('js'), scope=singleton)
    binder.bind(StaticFileService, to=get_by_name('sfs'), scope=singleton)


def start(injector: Injector):
    ms: ServerModuleService = get_by_name('ms')
    ms.set_injector(injector)

    ms.refresh_modules()
    ms.start_all()
