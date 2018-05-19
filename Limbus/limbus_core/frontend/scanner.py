# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod


class Scanner(metaclass=ABCMeta):
    EOF = None

    def __init__(self, source):
        self.source = source
        self.cur_token = None

    def current_token(self):
        return self.cur_token

    def next_token(self):
        self.cur_token = self.extract_token()
        return self.cur_token

    @abstractmethod
    def extract_token(self):
        raise NotImplementedError()

    def current_char(self):
        return self.source.current_char()

    def next_char(self):
        return self.source.next_char()
