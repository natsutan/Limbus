# -*- coding: utf-8 -*-
from . backend import Backend
from .. message import Message, MessageType


class Executer(Backend):
    def __init__(self):
        self.execution_count = 0
        self.runtime_error = 0
        super().__init__()

    def process(self, icode, symtab):
        ec = 0
        re = 0
        msg = Message(MessageType.EXECUTE_SUMMARY, (ec, re))
        self.send_message(msg)
