# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod


class SymTabStackIF(metaclass=ABCMeta):

    @abstractmethod
    def get_current_nesting_level(self):
        raise NotImplementedError()

    @abstractmethod
    def get_local_symtab(self):
        raise NotImplementedError()

    @abstractmethod
    def enter_local(self):
        raise NotImplementedError()

    @abstractmethod
    def lookup_local(self, name):
        raise NotImplementedError()

    @abstractmethod
    def lookup(self, name):
        raise NotImplementedError()


class SymTabIF(metaclass=ABCMeta):

    @abstractmethod
    def get_nesting_level(self):
        raise NotImplementedError()

    @abstractmethod
    def enter(self, name):
        raise NotImplementedError()

    @abstractmethod
    def lookup(self, name):
        raise NotImplementedError()

    @abstractmethod
    def get_sorted_entries(self):
        raise NotImplementedError()


class SynTabEntryIF(metaclass=ABCMeta):
    @abstractmethod
    def get_name(self):
        raise NotImplementedError()

    @abstractmethod
    def get_symtab(self):
        raise NotImplementedError()

    @abstractmethod
    def append_line_number(self, line_number):
        raise NotImplementedError()

    @abstractmethod
    def get_line_numbers(self):
        raise NotImplementedError()

    @abstractmethod
    def set_attribute(self, key, value):
        raise NotImplementedError()

    @abstractmethod
    def get_attribute(self, key):
        raise NotImplementedError()
