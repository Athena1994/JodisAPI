
from jodiscore.dataobjects.module_identifier import ModuleIdentifier
from jodiscore.server.module.datatypes.error import Error
from jodiscore.server.module.module_control import ModuleControl

from jodisutils.model_managing.attribute import Attribute
from jodisutils.model_managing.subject import Subject


class ServerModule(Subject):
    id = Attribute('id', ModuleIdentifier, primary_key=True)

    description = Attribute('description', str, 'No description provided')

    control = Attribute('control', ModuleControl, None, True)

    error = Attribute('error', Error, None, True)

    def __str__(self):
        return f"(ServerModule: {self.id})"
