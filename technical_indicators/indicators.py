import abc
import copy
import unittest
from abc import abstractmethod
from collections.abc import Sequence

import pandas as pd
import typing

from pandas import DataFrame

"""
    Specific indicator logic and parameter descriptions are wrapped in 
    `IndicatorPrototype` implementations. These provide a matching 
    `IndicatorDesc` object, which in turn can be used to instantiate actual 
    indicator objects.     
"""


class Indicator:
    def __init__(self,
                 name: str,
                 params: dict,
                 fct: typing.Callable[[dict, DataFrame], DataFrame],
                 skip_num: int,
                 norm_factor: float):
        self._name = name
        self._params = params
        self._fct = fct
        self._skip_num = skip_num
        self._norm_factor = norm_factor

    def apply(self, df: DataFrame) -> None:
        self._fct(self._params, df)

    def get_skip_num(self) -> int:
        return self._skip_num

    def get_norm_factor(self) -> float:
        return self._norm_factor


class IndicatorParameterDescription(typing.NamedTuple):
    name: str
    min_val: float
    max_val: float
    default_val: float
    data_type: str


class IndicatorDescription:
    def __init__(self, name: str,
                 params: typing.List[IndicatorParameterDescription],
                 fct: typing.Callable[[dict, DataFrame], DataFrame],
                 norm_factor: float = 1,
                 skip_field: str = None):
        self._name = name
        self._params_description = copy.deepcopy(params)
        self._fct = fct
        self._skip_parameter = skip_field
        self._norm_factor = norm_factor

    def get_parameter_descriptions(self) \
            -> typing.List[IndicatorParameterDescription]:
        return copy.deepcopy(self._params_description)

    def create_indicator(self, parameter_values: dict) -> Indicator:
        skip_cnt = 0 if self._skip_parameter is None \
            else parameter_values[self._skip_parameter]

        return Indicator(self._name,
                         parameter_values,
                         self._fct,
                         skip_cnt,
                         self._norm_factor)

class IndicatorPrototype:

    @abstractmethod
    def get_descriptor(self) -> IndicatorDescription:
        yield

    @abstractmethod
    def apply_to_df(self, params: dict, df: DataFrame) -> None:
        yield


#def instantiate(descriptors: [IndicatorDesc],
#                params: [[(str, float, float)]]):
#    return [desc.create_indicator(param) for desc, param in zip(descriptors,
#    params)]


#def apply(df: pd.DataFrame,
#          indicators: typing.List[Indicator]) -> tuple[pd.DataFrame,
    #          typing.List[float]]:
    #
    # features = [ind.calculate(df) for ind in indicators]
    # features = [ind if isinstance(ind, Sequence) else [ind]
    #             for ind in features]
    # features = [ind for seq in features for ind in seq]
    # features_df = pd.DataFrame(features).T
    #
    # norm_fct = [ind.get_norm_factor() for ind in indicators]
    # norm_fct = [fct if isinstance(fct, Sequence) else [fct]
    #             for fct in norm_fct]
    # norm_fct = [fct for seq in norm_fct for fct in seq]
    #
    # return features_df, norm_fct


class DummyIndicator(IndicatorPrototype):

    def __init__(self, skip_f):
        super().__init__()

        self.params = [
                IndicatorParameterDescription("a", 0, 10, 4, 'int'),
                IndicatorParameterDescription("b", -1, 1, 0.2, 'float'),
            ]
        self._skip_f = skip_f

    def apply_to_df(self, params: dict, df: DataFrame):
        df['v'] = params['b'] \
                  + df['w'].rolling(window=params['a'])\
                           .sum()

    def get_descriptor(self) -> IndicatorDescription:
        return IndicatorDescription(
            "dummy",
            params=self.params,
            fct=self.apply_to_df,
            norm_factor=3,
            skip_field=self._skip_f
        )


class TestIndicators(unittest.TestCase):
    def test(self):
        indicator_prototype = DummyIndicator(skip_f=None)
        desc = indicator_prototype.get_descriptor()
        self.assertListEqual(indicator_prototype.params,
                             desc.get_parameter_descriptions())
        params = dict([(p.name, p.default_val) for p in
                       desc.get_parameter_descriptions()])
        self.assertEqual(4, params['a'])
        self.assertEqual(0.2, params['b'])
        indicator = desc.create_indicator(params)
        self.assertEqual(0, indicator.get_skip_num())
        self.assertEqual(3, indicator.get_norm_factor())
        df = DataFrame(columns=['w'])
        df['w'] = range(15)
        indicator.apply(df)

        indicator_prototype = DummyIndicator(skip_f='a')
        desc = indicator_prototype.get_descriptor()
        self.assertListEqual(indicator_prototype.params,
                             desc.get_parameter_descriptions())
        params = {'a': 5, 'b': 0}
        indicator = desc.create_indicator(params)
        self.assertEqual(5, indicator.get_skip_num())
        self.assertEqual(3, indicator.get_norm_factor())
        df = DataFrame(columns=['w'])
        df['w'] = range(15)
        indicator.apply(df)
