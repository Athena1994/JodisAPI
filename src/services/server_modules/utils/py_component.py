from pathlib import Path


from utils.config.decorator import config
from utils.config.attribute import Attribute


@config
class PyComponent:
    file: Path = Attribute(required=True, json_type=str)
    class_name: str = Attribute('class', required=True)
