

class Attribute(property):

    def __init__(self,
                 name: str, type_: type,
                 default: object = None,
                 nullable=False,
                 primary_key=False):
        super().__init__(self.__get__, self.__set__)

        self._name = name
        self._default = default
        self._nullable = nullable
        self._type = type_
        self._field_name = None
        self._primary_key = primary_key

        if self._primary_key and self._nullable:
            raise ValueError('Primary key cannot be nullable!')

    def get_field_name(self, instance, att_name: str):
        if self._field_name is None:
            self._field_name = ""
        return self._field_name

    def __get__(self, instance, owner):
        if self._name not in instance.__dict__:
            raise AttributeError(f'Attribute {self._name} not initialized!')
        return instance.__dict__[self._name]

    def __set__(self, instance, value):
        if value is None and not self._nullable:
            raise ValueError(f'Attribute {self._name} cannot be None!')

        if not isinstance(value, self._type):
            raise ValueError(f'Attribute {self._name} must be of '
                             f'type {self._type}')

        callback = getattr(instance, 'on_attribute_changed', None)
        if (self._name in instance.__dict__) and callback:
            callback(self._name, instance.__dict__[self._name], value)

        instance.__dict__[self._name] = value
