

from src.utils.model_managing.attribute import Attribute


class Subject:

    def __init__(self, **kwargs: dict) -> None:

        # get all Attribute fields and initialize them according to kwargs and
        # default values
        self._attributes_dict \
            = {k: v for k, v in dict(type(self).__dict__).items()
               if isinstance(v, Attribute)}

        primary_key = [v._name for v in self._attributes_dict.values()
                       if v._primary_key]
        if len(primary_key) != 1:
            raise ValueError('Subject must have exactly one primary key!')

        self._primary_key = primary_key[0]

        for k, att in self._attributes_dict.items():
            if k in kwargs:
                setattr(self, k, kwargs[k])
            elif att._default is not None or att._nullable:
                setattr(self, k, att._default)
            else:
                raise ValueError(f'Initial value for attribute {k} not '
                                 'provided!')

    def on_attribute_changed(self, name: str, old_value: object,
                             new_value: object) -> None:
        pass

    def get_primary_key(self) -> object:
        return getattr(self, self._primary_key)
