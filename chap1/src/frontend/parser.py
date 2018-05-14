# -*- coding: utf-8 -*-

# package wci.frontend;
# import wci.intermediate.ICode;
# import wci.intermediate.SymTab;
from abc import ABCMeta, abstractmethod


class Parser(metaclass=ABCMeta):
    def __init__(self, scanner):
        self.symTab = None
        self.scanner = scanner
        self.iCode = None

    @abstractmethod
    def parse(self):
        raise NotImplementedError()

    @abstractmethod
    def get_error_count(self):
        raise NotImplementedError()

    def current_token(self):
        return self.scanner.cuurent_token()

    def next_token(self):
        return self.scanner.next_token()


