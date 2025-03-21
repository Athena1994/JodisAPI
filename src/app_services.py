
from app_config import AppConfig
from interface.services.client_connection_service import ClientConnectionService
from interface.services.client_request_service import ClientRequestService
from interface.services.module_service import ModuleService
from interface.services.update_event_service import UpdateEventService
from utils.db.db_context import DBContext
from utils.model_managing.subject_manager import SubjectManager

from flask_injector import singleton

_services = {}


def get(name: str):
    return _services[name]


def init(cfg: AppConfig):
    _services['sm'] = SubjectManager()
    _services['db'] = DBContext(cfg.db)
    _services['ues'] = UpdateEventService(_services['db'], _services['sm'])
    _services['ccs'] = ClientConnectionService(_services['sm'])
    _services['crs'] = ClientRequestService(_services['ccs'])
    _services['ms'] = ModuleService()


def flask_injector_configure(binder):
    binder.bind(DBContext, to=get('db'), scope=singleton)
    binder.bind(ClientConnectionService, to=get('ccs'), scope=singleton)
    binder.bind(ClientRequestService, to=get('crs'), scope=singleton)
    binder.bind(SubjectManager, to=get('sm'), scope=singleton)
    binder.bind(ModuleService, to=get('ms'), scope=singleton)
