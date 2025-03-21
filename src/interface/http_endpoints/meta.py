
import logging
from flask import Blueprint
from injector import inject

from interface.services.module_service import ModuleService

meta_pb = Blueprint('meta', __name__)


@meta_pb.route('/meta/version', methods=['GET'])
@inject
def get_version(ms: ModuleService):
    return ms.get_version()


@meta_pb.route('/meta/modules', methods=['GET'])
@inject
def get_modules(ms: ModuleService):
    return ms.get_modules()
