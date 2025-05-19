

from utils.config import config, Attribute


@config
class A:
    a: int = Attribute()


@config
class B:
    b: A = Attribute()


conf = {'b': {'a': 1}}


obj = B(**conf).b

print(obj.a)