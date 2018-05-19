# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from .. message import MessageProducer, MessageHandler


class Backend(MessageProducer, metaclass=ABCMeta):
    def __init__(self, icode, symtab):
        self.iCode = icode
        self.symTab = symtab
        self.message_handler = MessageHandler()

    @abstractmethod
    def process(self):
        raise NotImplementedError()

    # delegate
    def add_message_listener(self, listener):
        self.message_handler.add_message_listener(listener)

    def remove_message_listener(self, listener):
        self.message_handler.remove_message_listener(listener)

    def send_message(self, message):
        self.message_handler.send_message(message)
