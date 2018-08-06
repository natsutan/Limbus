# -*- coding: utf-8 -*-
from .executor import Executor
from .codegenerator import CodeGeneretor


class BackendFactory:
    def create_backend(self, operation):
        if operation == 'compile':
            return CodeGeneretor()
        elif operation == 'execute':
            return Executer(None)
        else:
            raise ValueError(operation)


def object_default_value(typespec):
    base_type = typespec.base_type()
    if base_type == Predefined.integer_type:
        return 0
    elif base_type == Predefined.real_type:
        return 0.0
    elif base_type == Predefined.boolean_type:
        return False
    elif base_type == Predefined.char_type:
        return "#"
    else:
        return '#'
