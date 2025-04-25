
from app_config import AppConfig
from services.client_connection_service import ClientConnectionService
from services.client_request_service import ClientRequestService
from services.server_module_service import ServerModuleService
from services.update_event_service import UpdateEventService
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
    _services['ms'] = ServerModuleService(_services['sm'])


def flask_injector_configure(binder):
    binder.bind(DBContext, to=get('db'), scope=singleton)
    binder.bind(ClientConnectionService, to=get('ccs'), scope=singleton)
    binder.bind(ClientRequestService, to=get('crs'), scope=singleton)
    binder.bind(SubjectManager, to=get('sm'), scope=singleton)
    binder.bind(ServerModuleService, to=get('ms'), scope=singleton)
