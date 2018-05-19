# -*- coding: utf-8 -*-
from . backend import Backend


class CodeGeneretor(Backend):
    def __init__(self):
        self.execution_count = 0
        self.runtime_error = 0
        super(Backend, self).__init__()

    def process(self, icode, symtab):
        raise NotImplemented()

