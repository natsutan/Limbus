# -*- coding: utf-8 -*-
from .executer import Executer
from .codegenerator import CodeGeneretor


class BackendFactory:
    def create_backend(self, operation):
        if operation == 'compile':
            return CodeGeneretor()
        elif operation == 'execute':
            return Executer()
        else:
            raise ValueError(operation)

