
from dataclasses import dataclass
from typing import Iterable, List
from flask import request


@dataclass
class Param:
    name: str
    type_: type = None
    collection: bool = False
    flag: bool = False


def get_request_parameter(parameter: Param) -> object:
    if parameter.name not in request.json:
        if parameter.flag:
            return False
        raise ValueError(f"Missing parameter: {parameter.name}")

    value = request.json[parameter.name]

    if parameter.collection:
        if not isinstance(value, Iterable):
            raise ValueError(f"'{parameter.name}' expected to be iterable")
    else:
        value = [value, ]

    if (parameter.type_ is not None
       and not all(isinstance(v, parameter.type_) for v in value)):
        raise ValueError(f"value in parameter {parameter.name} has not "
                         f"expected type ({parameter.type_.__name__})")

    return request.json[parameter.name]


def get_request_parameters(*parameters: List[Param]) -> tuple:
    return (get_request_parameter(p) for p in parameters)
