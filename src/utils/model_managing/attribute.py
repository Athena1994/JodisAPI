

class Attribute(property):

    def __init__(self,
                 name: str, type_: type,
                 default: object = None,
                 nullable=False,
                 primary_key=False,
                 auto_uid=False):
        super().__init__(self.__get__, self.__set__)

        self._name = name
        self._default = default
        self._nullable = nullable
        self._type = type_
        self._field_name = None
        self._primary_key = primary_key
        self._auto_uid = auto_uid

        if self._auto_uid:
            if not self._primary_key:
                raise ValueError('Auto uid must be primary key!')
            if not isinstance(self._auto_uid, int):
                raise ValueError('Auto uid must be of type int!')
            if nullable:
                raise ValueError('Auto uid cannot be nullable!')
            if default is not None:
                raise ValueError('Auto uid cannot have default value!')

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

        if value is not None and not isinstance(value, self._type):
            raise ValueError(f'Attribute {self._name} must be of '
                             f'type {self._type}')

        callback = getattr(instance, 'on_attribute_changed', None)
        if (self._name in instance.__dict__) and callback:
            callback(self._name, instance.__dict__[self._name], value)

        instance.__dict__[self._name] = value
