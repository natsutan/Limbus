# -*- coding: utf-8 -*-
from . backend import Backend
from .. message import Message, MessageType


class Executer(Backend):
    def __init__(self, icode, symtab):
        self.execution_count = 0
        self.runtime_error = 0
        super(Backend, self).__init__(icode, symtab)

    def process(self):
        ec = 0
        re = 0
        msg = Message(MessageType.EXECUTE_SUMMARY, (ic, re))
        self.send_message(msg)
