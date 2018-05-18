# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from .. message import MessageProducer, MessageHandler


class Backend(metaclass=ABCMeta, MessageProducer):
    def __init__(self, scanner):
        self.symTab = None
        self.scanner = scanner
        self.iCode = None
        self.message_handler = MessageHandler()

    @abstractmethod
    def process(self):
        raise NotImplementedError()

