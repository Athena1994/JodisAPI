from pathlib import Path


from jodisutils.config.decorator import config
from jodisutils.config.attribute import Attribute


@config
class PyComponent:
    file: Path = Attribute(required=True, json_type=str)
    class_name: str = Attribute('class', required=True)
