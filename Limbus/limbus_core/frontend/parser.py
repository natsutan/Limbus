# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from .. message import MessageProducer, MessageHandler
from .. intermidiate.symtabstack_impl import SymTabStack
from limbus_core.intermidiate.iCode_factory import iCodeFactory

class Parser(MessageProducer, metaclass=ABCMeta):
    symtab_stack = SymTabStack()
    iCode = iCodeFactory().create()


    def __init__(self, scanner):
        self.symTab = None
        self.scanner = scanner
        self.message_handler = MessageHandler()

    @abstractmethod
    def parse(self):
        raise NotImplementedError()

    @abstractmethod
    def get_iCode(self):
        raise NotImplementedError()

    @abstractmethod
    def get_symTab(self):
        raise NotImplementedError()

    @abstractmethod
    def get_error_count(self):
        raise NotImplementedError()

    def current_token(self):
        return self.scanner.current_token()

    def next_token(self):
        return self.scanner.next_token()

    def get_scanner(self):
        return self.scanner

    # delegate
    def add_message_listener(self, listener):
        self.message_handler.add_message_listener(listener)

    def remove_message_listener(self, listener):
        self.message_handler.remove_message_listener(listener)

    def send_message(self, message):
        self.message_handler.send_message(message)
