
from utils.config.decorator import config, schema
from utils.config.attribute import Attribute


@config
class WebComponent:
    module_url: str = Attribute('module', required=True)
    component_class: str = Attribute('class', required=True)

    @schema
    def secondary_schema(self) -> dict:
        return {
            'type': 'string'
        }
