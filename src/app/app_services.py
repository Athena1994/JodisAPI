
from typing import TypeVar
from injector import Injector
from flask_injector import singleton

from app.app_config import AppConfig

from jodiscore.server.job_provider.job_provider_control\
    import JobProviderControl
from jodisutils.static_file_provider import StaticFileProvider
from services.client_connection_service import ClientConnectionService
from services.client_request_service import ClientRequestService
from services.job_service import JobService
from services.server_module_service import ServerModuleService
from services.update_event_service import UpdateEventService

from jodisutils import injector
from jodisutils.db.db_context import DBContext
from jodisutils.model_managing.subject_manager import SubjectManager


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
    _services['ccs'] = ClientConnectionService()
    _services['crs'] = ClientRequestService(_services['ccs'])
    _services['ms'] = ServerModuleService(_services['sm'])
    _services['js'] = JobService(_services['db'])
    _services['sfp'] \
        = StaticFileProvider(f"{cfg.server.host}:{cfg.server.port}", 'statics')
    _services['jpc'] = JobProviderControl()

    for name, service in _services.items():
        i.bind(service.__class__, to=service)


def flask_injector_configure(binder):
    binder.bind(DBContext, to=get_by_name('db'), scope=singleton)
    binder.bind(ClientConnectionService, to=get_by_name('ccs'), scope=singleton)
    binder.bind(ClientRequestService, to=get_by_name('crs'), scope=singleton)
    binder.bind(SubjectManager, to=get_by_name('sm'), scope=singleton)
    binder.bind(ServerModuleService, to=get_by_name('ms'), scope=singleton)
    binder.bind(JobService, to=get_by_name('js'), scope=singleton)
    binder.bind(StaticFileProvider, to=get_by_name('sfp'), scope=singleton)
    binder.bind(UpdateEventService, to=get_by_name('ues'), scope=singleton)


def start(injector: Injector):
    ms: ServerModuleService = get_by_name('ms')
    ms.set_injector(injector)

    ms.refresh_modules()
    ms.start_all()
