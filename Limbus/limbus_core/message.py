# -*- coding: utf-8 -*-
from enum import Enum,  auto
from abc import ABCMeta, abstractmethod


class MessageType(Enum):
    DUMMY = auto()
    SOURCE_LINE = auto()
    SYNTAX_ERROR = auto()
    PARSER_SUMMARY = auto()
    INTERPRETER_SUMMARY = auto()
    EXECUTE_SUMMARY = auto()
    COMPILER_SUMMARY = auto() 
    MISCELLANEOUS = auto() 
    MSG_TOKEN = auto() 
    ASSIGN = auto() 
    FETCH = auto() 
    BREAKPOINT = auto() 
    RUNTIME_ERROR = auto() 
    CALL = auto() 
    RETURN = auto()


class Message:
    def __init__(self, mtype, body):
        self.type = mtype
        self.body = body


class MessageProducer(metaclass=ABCMeta):
    @abstractmethod
    def add_message_listener(self, listener):
        raise NotImplementedError()

    @abstractmethod
    def remove_message_listener(self, listener):
        raise NotImplementedError()

    @abstractmethod
    def send_message(self, message):
        raise NotImplementedError()


class MessageListener(metaclass=ABCMeta):
    @abstractmethod
    def message_received(self, message):
        raise NotImplementedError()


class MessageHandler:
    def __init__(self):
        self.msg = None
        self.listener = []

    def add_message_listener(self, listener):
        self.listener.append(listener)

    def remove_message_listener(self, listener):
        self.listener.remove(listener)

    def send_message(self, message):
        self.msg = message
        self.notify_listener()

    def notify_listener(self):
        for l in self.listener:
            l.message_received(self.msg)

