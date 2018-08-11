# -*- coding: utf-8 -*-

class BackendFactory:
    def create_backend(self, operation):
        from executor import Executor
        from backend import CodeGeneretor
        if operation == 'compile':
            return CodeGeneretor()
        elif operation == 'execute':
            return Executor(None)
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
