from model.local_model.module_interface.sub_module import SubModule


class BaseModule:

    def __init__(self):
        self._sub_modules = list()

    def register_sub_module(self, sub_module: SubModule) -> None:
        self._sub_modules.append(sub_module)
