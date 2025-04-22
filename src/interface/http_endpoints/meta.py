import json
import logging
from flask import Blueprint
from injector import inject

from interface.data_objects import ModuleDO
from interface.http_endpoints.http_utils import ok
from services.server_module_service import ServerModuleService
from utils.http_utils import Param, get_request_parameter

meta_pb = Blueprint('meta', __name__)


@meta_pb.route('/meta/version', methods=['GET'])
@inject
def get_version(ms: ServerModuleService):
    return ms.get_version()


@meta_pb.route('/meta/module/reload', methods=['POST'])
@inject
def reload_module(sm: ServerModuleService):
    module_name: str = get_request_parameter(
         Param('moduleName', type_=str))

    logging.info(f"Reloading module '{module_name}'")

    module = sm.reload_module(module_name)

    return [ModuleDO.from_model(*sm.get_module(module.name))]


@meta_pb.route('/meta/modules', methods=['GET'])
@inject
def get_modules(sm: ServerModuleService):
    r = [ModuleDO.from_model(
        m,
        [sm.get_module_version(m.name, ver)
         for ver in m.version_ids.keys()],
        v) for m, v in sm.get_modules()]
    return r
