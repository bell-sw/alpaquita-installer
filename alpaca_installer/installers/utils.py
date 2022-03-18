from typing import Type, TypeVar

TV = TypeVar(name='TV')


def read_key_or_fail(data: dict, key: str, value_type: Type[TV]) -> TV:
    value = data.get(key, value_type())
    if not isinstance(value, value_type):
        raise ValueError("'{}' must be of type '{}'".format(key, str(value_type)))
    return value
