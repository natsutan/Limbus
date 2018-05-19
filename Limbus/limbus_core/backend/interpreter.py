# -*- coding: utf-8 -*-
from . backend import Backend
from .. message import Message, MessageType


class Interpreter(Backend):
    def __init__(self, icode, symtab):
        self.instruction_count = 0
        super(Backend, self).__init__(icode, symtab)

    def process(self):
        ic = 0
        msg = Message(MessageType.INTERPRETER_SUMMARY, ic)
        self.send_message(msg)
