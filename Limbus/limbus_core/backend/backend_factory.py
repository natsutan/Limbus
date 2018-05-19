# -*- coding: utf-8 -*-
from .executer import Executer
from .codegenerator import CodeGeneretor


class BackendFactory:
    def create_backend(self, operation):
        if operation == 'compile':
            return CodeGeneretor(None, None)
        elif operation == 'execute':
            return Executer(None, None)
        else:
            raise ValueError(operation)

