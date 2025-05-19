
from dataclasses import dataclass
import functools
import inspect
from typing import Iterable, List
from flask import request

from interface.http_endpoints.http_utils import bad_request


def inject_query_parameters(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        r_args = dict(map(lambda i: (i[0].lower().replace('-', '_'), i[1]),
                          request.args.items()))

        sig = inspect.signature(func)

        invalid_params = []

        for key, value in r_args.items():
            if key not in sig.parameters:
                invalid_params.append(key)
            else:
                try:
                    # convert to the expected type
                    param = sig.parameters[key]
                    if param.annotation is not inspect.Parameter.empty:
                        r_args[key] = param.annotation(value)
                except Exception as e:
                    return bad_request(
                        f"Invalid parameter type for '{key}': {str(e)}")

        if len(invalid_params) > 0:
            return bad_request("Unexpected request parameters: " +
                               ', '.join(invalid_params))

        kwargs.update(r_args)

        return func(*args, **(kwargs))

    return wrapper


@dataclass
class Param:
    name: str
    type_: type = None
    collection: bool = False
    flag: bool = False
    default: object | None = None
    optional: bool = False


def get_request_parameter(parameter: Param) -> object:
    if parameter.name not in request.json:
        if parameter.default is not None:
            return parameter.default

        if parameter.optional:
            return None

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
