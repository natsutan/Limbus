# -*- coding: utf-8 -*-
from . backend import Backend
from .. message import Message, MessageType


class CodeGeneretor(Backend):
    def __init__(self):
        self.execution_count = 0
        self.runtime_error = 0
        super().__init__()

    def process(self, icode, symtab):
        ec = 0
        msg = Message(MessageType.COMPILER_SUMMARY, ec)
        self.send_message(msg)

